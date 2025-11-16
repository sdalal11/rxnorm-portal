# Backend modifications for api_server.py to support multiple folder assignments

# Add these imports at the top if not already present
import json

# Add this function after the database setup functions (around line 350)
def get_user_assigned_folders(username):
    """Get the assigned folders for a user"""
    try:
        # First try to get from assigned_folders column (new approach)
        result = execute_query(
            'SELECT assigned_folders FROM users WHERE username = ?', 
            (username,), 
            fetch_one=True
        )
        
        if result and result[0]:
            # If it's a JSONB array, return it directly
            if isinstance(result[0], list):
                return result[0]
            # If it's a JSON string, parse it
            elif isinstance(result[0], str):
                try:
                    return json.loads(result[0])
                except:
                    # If parsing fails, maybe it's a comma-separated string
                    return [int(x.strip()) for x in result[0].split(',') if x.strip().isdigit()]
            # If it's a single number (old format), convert to list
            elif isinstance(result[0], int):
                return [result[0]]
        
        # Fallback to old assigned_folder column if new one doesn't exist
        result = execute_query(
            'SELECT assigned_folder FROM users WHERE username = ?', 
            (username,), 
            fetch_one=True
        )
        
        if result and result[0]:
            # Handle different data types in assigned_folder
            if isinstance(result[0], list):
                return result[0]
            elif isinstance(result[0], str):
                try:
                    # Try parsing as JSON first
                    return json.loads(result[0])
                except:
                    # If not JSON, try comma-separated
                    if ',' in result[0]:
                        return [int(x.strip()) for x in result[0].split(',') if x.strip().isdigit()]
                    # If single number as string
                    elif result[0].isdigit():
                        return [int(result[0])]
            elif isinstance(result[0], int):
                return [result[0]]
        
        # If no assignments found, return empty list
        return []
        
    except Exception as e:
        print(f"⚠️ Error getting user assigned folders: {e}")
        return []

def set_user_assigned_folders(username, folder_list):
    """Set the assigned folders for a user"""
    try:
        # Convert list to JSON string for storage
        folders_json = json.dumps(folder_list)
        
        # Try to update assigned_folders column first
        try:
            execute_query(
                'UPDATE users SET assigned_folders = ? WHERE username = ?',
                (folders_json, username)
            )
            return True
        except:
            # If assigned_folders column doesn't exist, try assigned_folder
            execute_query(
                'UPDATE users SET assigned_folder = ? WHERE username = ?',
                (folders_json, username)
            )
            return True
            
    except Exception as e:
        print(f"⚠️ Error setting user assigned folders: {e}")
        return False

# Modify the login_user function (around line 517)
# Replace the existing login_user function with this:
@app.route('/users/login', methods=['POST', 'OPTIONS'])
def login_user():
    """Authenticate user login"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        login_data = request.get_json()
        username = login_data.get('username', '').strip().lower()
        password = login_data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Check if user exists in database and password matches
        user = get_user(username)
        if not user or user.get('password') != password:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Get user's assigned folders
        assigned_folders = get_user_assigned_folders(username)
        
        # Update last login in database
        update_last_login(username)
        
        print(f"✅ User logged in: {username} with folders: {assigned_folders}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'email': user['email'],
                'name': user['name'],
                'assigned_folders': assigned_folders  # Include folder assignments
            }
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': str(e)}), 500

# Add new endpoint to manage folder assignments
@app.route('/admin/assign-folders', methods=['POST', 'OPTIONS'])
def assign_folders_to_user():
    """Assign multiple folders to a user"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        folders = data.get('folders', [])
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        if not isinstance(folders, list):
            return jsonify({'error': 'Folders must be a list'}), 400
        
        # Validate that folders are integers
        try:
            folder_numbers = [int(f) for f in folders]
        except ValueError:
            return jsonify({'error': 'All folder values must be integers'}), 400
        
        # Check if user exists
        user = get_user(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Assign folders to user
        success = set_user_assigned_folders(username, folder_numbers)
        
        if success:
            print(f"✅ Assigned folders {folder_numbers} to user: {username}")
            return jsonify({
                'success': True,
                'message': f'Successfully assigned {len(folder_numbers)} folders to {username}',
                'username': username,
                'assigned_folders': folder_numbers
            })
        else:
            return jsonify({'error': 'Failed to assign folders'}), 500
            
    except Exception as e:
        print(f"❌ Error assigning folders: {e}")
        return jsonify({'error': str(e)}), 500

# Add endpoint to get user's current folder assignments
@app.route('/users/folders/<username>', methods=['GET', 'OPTIONS'])
def get_user_folders(username):
    """Get assigned folders for a specific user"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        username = username.strip().lower()
        
        # Check if user exists
        user = get_user(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get assigned folders
        assigned_folders = get_user_assigned_folders(username)
        
        return jsonify({
            'success': True,
            'username': username,
            'assigned_folders': assigned_folders,
            'total_folders': len(assigned_folders)
        })
        
    except Exception as e:
        print(f"❌ Error getting user folders: {e}")
        return jsonify({'error': str(e)}), 500

# Update the home endpoint to include new endpoints
# Find the home function and add these new endpoints:
# Add to the endpoints dictionary:
'admin_assign_folders': '/admin/assign-folders',
'user_folders': '/users/folders/<username>',
