from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import subprocess
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Available folders for sequential assignment
AVAILABLE_FOLDERS = [
    "100-200", "200-300", "300-400", "400-500", "500-600",
    "600-700", "700-800", "800-900", "900-1000"
]

class FolderManager:
    """Manages sequential folder assignment based on login timestamps"""
    
    def __init__(self):
        self.total_folders = len(AVAILABLE_FOLDERS)
    
    def get_next_assignment_order(self):
        """Get the next assignment order number by counting existing assignments"""
        assignment_count = 0
        for username, user_data in global_users.items():
            if 'assignment_order' in user_data and user_data['assignment_order'] is not None:
                assignment_count += 1
        return assignment_count + 1
    
    def assign_folder_to_user(self, username, login_timestamp):
        """Assign folder based on sequential order with cycling"""
        assignment_order = self.get_next_assignment_order()
        
        # Calculate folder index using modulo for cycling
        folder_index = (assignment_order - 1) % self.total_folders
        assigned_folder = AVAILABLE_FOLDERS[folder_index]
        
        print(f"🎯 Assigning folder '{assigned_folder}' to user '{username}' (Order: {assignment_order})")
        
        return {
            'folder': assigned_folder,
            'assignment_order': assignment_order,
            'timestamp': login_timestamp,
            'folder_index': folder_index
        }
    
    def get_folder_assignments(self):
        """Get all current folder assignments for admin view"""
        assignments = []
        for username, user_data in global_users.items():
            if 'assigned_folder' in user_data:
                assignments.append({
                    'username': username,
                    'name': user_data.get('name', 'N/A'),
                    'email': user_data.get('email', 'N/A'),
                    'assigned_folder': user_data.get('assigned_folder'),
                    'assignment_order': user_data.get('assignment_order'),
                    'login_timestamp': user_data.get('login_timestamp'),
                    'last_login': user_data.get('last_login')
                })
        
        # Sort by assignment order
        assignments.sort(key=lambda x: x.get('assignment_order', 0))
        return assignments

# Initialize folder manager
folder_manager = FolderManager()

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'message': 'RxNorm Document Processing API',
        'version': '1.2',  # Updated for database authentication
        'endpoints': {
            'health': '/health',
            'process': '/process-document',
            'azure_config': '/config/azure',
            'user_register': '/users/register',
            'user_login': '/users/login',
            'user_list': '/users/list'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'API server is running',
        'service': 'RxNorm Document Processor'
    })

# Replace the process_document function with this updated version:

@app.route('/process-document', methods=['POST', 'OPTIONS'])
def process_document():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        print("Processing document request received...")  # Debug log
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Processing file: {file.filename}")  # Debug log
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w+b') as temp_input:
            file.save(temp_input.name)
            temp_input_path = temp_input.name
        

        temp_output_dir = tempfile.mkdtemp()
        
        try:
            print(f"Running main.py with input: {temp_input_path}, output: {temp_output_dir}")

            # Run main.py with correct arguments
            result = subprocess.run([
                'python', 'main.py', 
                '--input', temp_input_path,
                '--output', temp_output_dir
            ], capture_output=True, text=True, timeout=60)
            
            print(f"main.py exit code: {result.returncode}")
            print(f"main.py stdout: {result.stdout}")
            print(f"main.py stderr: {result.stderr}")
            
            if result.returncode != 0:
                return jsonify({'error': f'Processing failed: {result.stderr}'}), 500
            
            # Read the output JSON file
            annotations = []
            try:
                # List files in output directory
                output_files = os.listdir(temp_output_dir)
                print(f"Files created in output directory: {output_files}")
                
                # Look for JSON files
                json_files = [f for f in output_files if f.endswith('.json')]
                
                if json_files:
                    # Read the first JSON file found
                    json_file_path = os.path.join(temp_output_dir, json_files[0])
                    print(f"Reading JSON output from: {json_file_path}")
                    
                    with open(json_file_path, 'r') as f:
                        output_data = json.load(f)
                    
                    # Convert main.py output to annotation format
                    annotations = convert_main_py_output_to_annotations(output_data)
                    print(f"Successfully loaded {len(annotations)} annotations from output file")
                else:
                    print("No JSON files found in output directory, trying to parse stdout...")
                    # Fallback to parsing stdout if no JSON files created
                    if result.stdout.strip():
                        try:
                            output_data = json.loads(result.stdout)
                            annotations = convert_main_py_output_to_annotations(output_data)
                        except json.JSONDecodeError:
                            annotations = parse_main_py_text_output(result.stdout)
                    
            except Exception as e:
                print(f"Error reading output files: {e}")
                # Try parsing stdout as fallback
                annotations = parse_main_py_text_output(result.stdout)
            
            return jsonify({
                'success': True,
                'annotations': annotations,
                'filename': file.filename,
                'processed_at': subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
            })
            
        finally:
            # Clean up temporary files and directories
            try:
                os.unlink(temp_input_path)
                print(f"Cleaned up temp input file: {temp_input_path}")
            except:
                pass
            
            try:
                # Clean up output directory and all files in it
                import shutil
                shutil.rmtree(temp_output_dir)
                print(f"Cleaned up temp output directory: {temp_output_dir}")
            except:
                pass
            
    except Exception as e:
        print(f"Error in process_document: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Replace the convert_main_py_output_to_annotations function with this:
def convert_main_py_output_to_annotations(output_data):
    """Convert main.py JSON output to annotation format"""
    annotations = []
    
    print(f"Converting main.py output: {output_data}")
    
    # Handle different possible output formats from main.py
    if isinstance(output_data, list):
        # If output is a list of medications
        for item in output_data:
            if isinstance(item, dict):
                # Extract the actual medication name from the complex object
                medication_name = (
                    item.get('text') or 
                    item.get('normalized_name') or 
                    item.get('medication') or 
                    item.get('name') or 
                    item.get('drug') or 
                    str(item)
                )
                
                # Clean up the medication name
                medication_name = medication_name.strip()
                
                annotations.append({
                    'text': medication_name,
                    'status': item.get('active_status', item.get('status', 'active')),
                    'confidence': item.get('confidence', 0.9),
                    'source': 'main.py',
                    'rxnorm_code': item.get('rx_cui', item.get('rxnorm_code', item.get('rxnorm', item.get('code'))))
                })
            else:
                # Handle simple string items
                annotations.append({
                    'text': str(item).strip(),
                    'status': 'active',
                    'confidence': 0.8,
                    'source': 'main.py',
                    'rxnorm_code': None
                })
    
    elif isinstance(output_data, dict):
        # If output is a dictionary with medications
        medications = output_data.get('medications', output_data.get('drugs', output_data.get('results', [])))
        
        if isinstance(medications, list):
            for med in medications:
                if isinstance(med, dict):
                    medication_name = (
                        med.get('text') or 
                        med.get('normalized_name') or 
                        med.get('medication') or 
                        med.get('name') or 
                        med.get('drug') or 
                        str(med)
                    )
                    
                    medication_name = medication_name.strip()
                    
                    annotations.append({
                        'text': medication_name,
                        'status': med.get('active_status', med.get('status', 'active')),
                        'confidence': med.get('confidence', 0.9),
                        'source': 'main.py',
                        'rxnorm_code': med.get('rx_cui', med.get('rxnorm_code', med.get('rxnorm', med.get('code'))))
                    })
        else:
            # Handle case where the main object itself is a medication
            if 'text' in output_data or 'normalized_name' in output_data:
                medication_name = (
                    output_data.get('text') or 
                    output_data.get('normalized_name') or 
                    str(output_data)
                )
                
                medication_name = medication_name.strip()
                
                annotations.append({
                    'text': medication_name,
                    'status': output_data.get('active_status', output_data.get('status', 'active')),
                    'confidence': output_data.get('confidence', 0.9),
                    'source': 'main.py',
                    'rxnorm_code': output_data.get('rx_cui', output_data.get('rxnorm_code'))
                })
    
    print(f"Processed {len(annotations)} annotations: {annotations}")
    return annotations

def parse_main_py_text_output(output):
    """Fallback: Parse text output from main.py"""
    annotations = []
    
    print(f"Parsing main.py text output: {repr(output)}")
    
    lines = output.strip().split('\n') if output.strip() else []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for medication-related patterns in the output
        if any(keyword in line.lower() for keyword in ['medication', 'drug', 'medicine', 'aspirin', 'metformin']):
            annotations.append({
                'text': line,
                'status': 'active',
                'confidence': 0.7,
                'source': 'main.py',
                'rxnorm_code': None
            })
    
    return annotations

# Database setup for persistent user storage
# For production: Use external database URL if available, fallback to local SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_FILE = os.environ.get('DATABASE_FILE', '/tmp/users.db') if not DATABASE_URL else None

def init_database():
    """Initialize database for user storage - supports both SQLite and PostgreSQL"""
    try:
        if DATABASE_URL:
            # Using external PostgreSQL database (persistent)
            import psycopg2
            
            print(f"🔗 Attempting to connect to external database...")
            print(f"📍 Database URL: {DATABASE_URL[:50]}...")  # Show partial URL for debugging
            
            # Try different connection methods for better compatibility
            try:
                # First try with the direct URL
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            except Exception as e1:
                print(f"⚠️  Direct connection failed: {e1}")
                
                # Try parsing the URL and connecting with individual parameters
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(DATABASE_URL)
                    
                    print(f"🔄 Trying parsed connection to {parsed.hostname}:{parsed.port}")
                    conn = psycopg2.connect(
                        host=parsed.hostname,
                        port=parsed.port,
                        database=parsed.path[1:],  # Remove leading /
                        user=parsed.username,
                        password=parsed.password,
                        sslmode='require'
                    )
                except Exception as e2:
                    print(f"⚠️  Parsed connection failed: {e2}")
                    
                    # Final fallback - try without SSL requirement
                    print("🔄 Trying connection without SSL requirement...")
                    conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
            
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            print("✅ Connected to external PostgreSQL database")
        else:
            # Using local SQLite database (ephemeral on free hosting)
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')
            print(f"⚠️  Using local SQLite database: {DATABASE_FILE}")
            print("⚠️  Warning: User data will be lost on container restart!")
        
        # Create default admin user if no users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            if DATABASE_URL:
                cursor.execute('''
                    INSERT INTO users (username, email, password, name, registered_at)
                    VALUES (%s, %s, %s, %s, %s)
                ''', ('admin', 'admin@rxnorm.com', 'admin123', 'System Administrator', datetime.now()))
            else:
                cursor.execute('''
                    INSERT INTO users (username, email, password, name, registered_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'admin@rxnorm.com', 'admin123', 'System Administrator', datetime.now()))
            print("✅ Created default admin user")
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized with {user_count + (1 if user_count == 0 else 0)} users")
        
    except Exception as e:
        print(f"⚠️ Error initializing database: {e}")

def get_db_connection():
    """Get database connection (PostgreSQL or SQLite)"""
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        return sqlite3.connect(DATABASE_FILE)

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute database query with proper parameter substitution"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            # PostgreSQL uses %s for all parameters
            if params:
                cursor.execute(query.replace('?', '%s'), params)
            else:
                cursor.execute(query)
        else:
            # SQLite uses ?
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        
        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        
        conn.commit()
        conn.close()
        return result
    except Exception as e:
        print(f"⚠️ Database error: {e}")
        return None

def get_user(username):
    """Get user from database"""
    try:
        result = execute_query('SELECT * FROM users WHERE username = ?', (username,), fetch_one=True)
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'password': result[3],
                'name': result[4],
                'registered_at': result[5],
                'last_login': result[6]
            }
        return None
    except Exception as e:
        print(f"⚠️ Error getting user: {e}")
        return None

def create_user(username, email, password, name):
    """Create new user in database"""
    try:
        execute_query('''
            INSERT INTO users (username, email, password, name)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password, name))
        return True
    except Exception as e:
        if "UNIQUE constraint" in str(e) or "duplicate key" in str(e):
            print(f"⚠️ User creation failed - duplicate entry: {e}")
        else:
            print(f"⚠️ Error creating user: {e}")
        return False

def update_last_login(username):
    """Update user's last login time"""
    try:
        execute_query('UPDATE users SET last_login = ? WHERE username = ?', 
                     (datetime.now(), username))
        return True
    except Exception as e:
        print(f"⚠️ Error updating last login: {e}")
        return False

def list_users():
    """List all users (admin function)"""
    try:
        results = execute_query('SELECT id, username, email, name, registered_at, last_login FROM users', 
                               fetch_all=True)
        
        if results:
            users = []
            for user_data in results:
                users.append({
                    'id': user_data[0],
                    'username': user_data[1],
                    'email': user_data[2],
                    'name': user_data[3],
                    'registered_at': user_data[4],
                    'last_login': user_data[5]
                })
            return users
        return []
    except Exception as e:
        print(f"⚠️ Error listing users: {e}")
        return []
        print(f"⚠️ Error getting all users: {e}")
        return []

# Initialize database on startup
init_database()

# Global configuration storage (in production, use a database)
global_config = {}
global_users = {}  # Store registered users

# User management endpoints
@app.route('/users/register', methods=['POST', 'OPTIONS'])
def register_user():
    """Register a new user"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        user_data = request.get_json()
        username = user_data.get('username', '').strip().lower()
        email = user_data.get('email', '').strip().lower()
        password = user_data.get('password', '')
        name = user_data.get('name', '').strip()
        
        if not all([username, email, password, name]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check if user already exists in database
        existing_user = get_user(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Check if email already exists in database
        try:
            email_check = execute_query('SELECT username FROM users WHERE email = ?', (email,), fetch_one=True)
            if email_check:
                return jsonify({'error': 'Email already registered'}), 409
        except Exception as e:
            print(f"⚠️ Error checking email: {e}")
        
        # Create user in database
        if create_user(username, email, password, name):
            print(f"📝 User registered in database: {username} ({email})")
            
            # Also add to global_users for compatibility (temporary)
            global_users[username] = {
                'username': username,
                'email': email,
                'password': password,
                'name': name,
                'registered_at': datetime.now().isoformat(),
                'last_login': None
            }
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'username': username,
                    'email': email,
                    'name': name
                }
            })
        else:
            return jsonify({'error': 'Registration failed. Please try again.'}), 500
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': str(e)}), 500

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
        
        # Generate precise login timestamp
        login_timestamp = datetime.now().isoformat()
        
        # Update last login in database
        update_last_login(username)
        
        # Also update global_users for compatibility (temporary)
        if username in global_users:
            global_users[username]['last_login'] = login_timestamp
            
            # Check if user already has a folder assigned
            if 'assigned_folder' not in global_users[username] or global_users[username]['assigned_folder'] is None:
                # Assign folder based on login order
                folder_assignment = folder_manager.assign_folder_to_user(username, login_timestamp)
                
                # Update user record with folder assignment
                global_users[username]['assigned_folder'] = folder_assignment['folder']
                global_users[username]['assignment_order'] = folder_assignment['assignment_order']
                global_users[username]['login_timestamp'] = login_timestamp
                
                print(f"🎯 New folder assignment - User: {username}, Folder: {folder_assignment['folder']}, Order: {folder_assignment['assignment_order']}")
            else:
                print(f"🔄 Existing user login - User: {username}, Folder: {global_users[username]['assigned_folder']}")
        
        print(f"✅ User logged in: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'email': user['email'],
                'name': user['name'],
                'assigned_folder': global_users[username].get('assigned_folder') if username in global_users else None,
                'assignment_order': global_users[username].get('assignment_order') if username in global_users else None,
                'login_timestamp': login_timestamp,
                'folder_count': len(AVAILABLE_FOLDERS)
            }
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/list', methods=['GET', 'OPTIONS'])
def list_users():
    """Get list of all registered users (for admin)"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        user_list = []
        for username, user_info in global_users.items():
            user_list.append({
                'username': user_info['username'],
                'email': user_info['email'],
                'name': user_info['name'],
                'registered_at': user_info['registered_at'],
                'last_login': user_info['last_login']
            })
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total': len(user_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/list', methods=['GET', 'OPTIONS'])
def get_users_list():
    """Get list of all registered users (for admin)"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        user_list = list_users()
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total': len(user_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/backup', methods=['GET', 'OPTIONS'])
def backup_users():
    """Get users data for backup/persistence"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        # Get all users from database
        all_users = list_users()
        users_json = json.dumps(all_users, separators=(',', ':'))
        return jsonify({
            'success': True,
            'users_backup': users_json,
            'total_users': len(all_users),
            'message': 'Database backup created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/folder-assignments', methods=['GET', 'OPTIONS'])
def get_folder_assignments():
    """Get folder assignments for admin dashboard"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        assignments = folder_manager.get_folder_assignments()
        
        # Calculate folder distribution stats
        folder_stats = {}
        for folder in AVAILABLE_FOLDERS:
            folder_stats[folder] = len([a for a in assignments if a['assigned_folder'] == folder])
        
        return jsonify({
            'success': True,
            'assignments': assignments,
            'total_users': len(assignments),
            'total_folders': len(AVAILABLE_FOLDERS),
            'folder_distribution': folder_stats,
            'available_folders': AVAILABLE_FOLDERS
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/folder-info', methods=['GET', 'POST', 'OPTIONS'])
def get_user_folder_info():
    """Get specific user's folder assignment info"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        if request.method == 'POST':
            data = request.get_json()
            username = data.get('username', '').strip().lower()
        else:
            username = request.args.get('username', '').strip().lower()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        user = global_users.get(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user_info': {
                'username': username,
                'name': user.get('name'),
                'assigned_folder': user.get('assigned_folder'),
                'assignment_order': user.get('assignment_order'),
                'login_timestamp': user.get('login_timestamp'),
                'last_login': user.get('last_login')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config/azure', methods=['POST', 'GET', 'OPTIONS'])
def azure_config():
    """Manage Azure configuration for document sharing"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    if request.method == 'POST':
        # Store Azure configuration (called by admin)
        try:
            config_data = request.get_json()
            global_config['azure'] = {
                'storageAccount': config_data.get('storageAccount'),
                'containerName': config_data.get('containerName'),
                'sasToken': config_data.get('sasToken'),  # In production, encrypt this
                'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
            }
            
            return jsonify({
                'success': True,
                'message': 'Azure configuration stored successfully'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'GET':
        # Retrieve Azure configuration (called by users)
        try:
            azure_config = global_config.get('azure', {})
            if azure_config:
                return jsonify({
                    'success': True,
                    'config': azure_config
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No Azure configuration found'
                }), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting RxNorm Document Processing API")
    print("=" * 50)
    
    # Get port from environment variable (Render requirement)
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'  # Required for Render
    
    print(f"📍 Server URL: http://{host}:{port}")
    print(f"🔍 Health check: http://{host}:{port}/health")
    print(f"📄 Process endpoint: http://{host}:{port}/process-document")
    print(f"💡 Root info: http://{host}:{port}/")
    print("=" * 50)
    print("🔥 Server is ready to process documents!")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=False)