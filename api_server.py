from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import subprocess
import json
import sqlite3
from datetime import datetime

# Database imports - psycopg2 for PostgreSQL/Supabase
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
    print("✅ psycopg2 imported successfully")
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("⚠️ psycopg2 not available - PostgreSQL connections will fail")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

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
        'version': '1.3',
        'endpoints': {
            'health': '/health',
            'database_debug': '/debug/database',
            'supabase_debug': '/debug/supabase',
            'process': '/process-document',
            'azure_config': '/config/azure',
            'user_register': '/users/register',
            'user_login': '/users/login',
            'user_list': '/users/list',
            'folder_assignments': '/users/folder-assignments',
            'admin_folder_assignments': '/admin/folder-assignments',
            'admin_emails': '/admin/emails'
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

@app.route('/debug/database', methods=['GET'])
def debug_database():
    """Database connection diagnostic endpoint"""
    try:
        db_info = {
            'database_url_set': bool(DATABASE_URL),
            'database_file': DATABASE_FILE,
            'connection_test': 'pending',
            'psycopg2_available': PSYCOPG2_AVAILABLE
        }
        
        if DATABASE_URL:
            db_info['database_url_prefix'] = DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL
            db_info['is_supabase'] = 'supabase.co' in DATABASE_URL
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM users;')
                user_count = cursor.fetchone()[0]
                conn.close()
                
                db_info.update({
                    'connection_test': 'success',
                    'database_version': version[:100],
                    'user_count': user_count,
                    'database_type': 'PostgreSQL'
                })
            except Exception as e:
                db_info.update({
                    'connection_test': 'failed',
                    'error': str(e)[:200],
                    'database_type': 'PostgreSQL (failed, may fallback to SQLite)'
                })
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users;')
                user_count = cursor.fetchone()[0]
                conn.close()
                
                db_info.update({
                    'connection_test': 'success',
                    'user_count': user_count,
                    'database_type': 'SQLite'
                })
            except Exception as e:
                db_info.update({
                    'connection_test': 'failed',
                    'error': str(e)[:200],
                    'database_type': 'SQLite (failed)'
                })
        
        return jsonify(db_info)
        
    except Exception as e:
        return jsonify({
            'error': 'Database diagnostic failed',
            'details': str(e)[:200]
        }), 500

@app.route('/debug/supabase', methods=['GET'])
def debug_supabase():
    """Test Supabase connection specifically"""
    original_database_url = os.environ.get('DATABASE_URL')
    
    if not original_database_url:
        return jsonify({
            'error': 'DATABASE_URL not set',
            'message': 'No DATABASE_URL environment variable found'
        }), 400
    
    result = {
        'database_url_prefix': original_database_url[:50] + "...",
        'is_supabase': 'supabase.co' in original_database_url,
        'psycopg2_available': PSYCOPG2_AVAILABLE,
        'connection_attempts': []
    }
    
    if not PSYCOPG2_AVAILABLE:
        return jsonify({
            **result,
            'error': 'psycopg2 not available',
            'message': 'Cannot test PostgreSQL connection without psycopg2'
        }), 500
    
    # Test different connection methods
    connection_configs = [
        {'name': 'Standard', 'params': {'sslmode': 'require'}},
        {'name': 'With timeout', 'params': {'sslmode': 'require', 'connect_timeout': 10}},
        {'name': 'Prefer SSL', 'params': {'sslmode': 'prefer', 'connect_timeout': 15}},
        {'name': 'Disable SSL', 'params': {'sslmode': 'disable', 'connect_timeout': 20}}
    ]
    
    for config in connection_configs:
        attempt = {'method': config['name'], 'success': False, 'error': None}
        
        try:
            conn = psycopg2.connect(original_database_url, **config['params'])
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s', ('users',))
            table_exists = cursor.fetchone()[0] > 0
            
            attempt.update({
                'success': True,
                'database_version': version[:100],
                'users_table_exists': table_exists
            })
            
            if table_exists:
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                attempt['user_count'] = user_count
            
            conn.close()
            result['connection_attempts'].append(attempt)
            break  # Stop at first successful connection
            
        except Exception as e:
            attempt['error'] = str(e)[:200]
            attempt['error_type'] = type(e).__name__
            result['connection_attempts'].append(attempt)
    
    # Determine overall result
    successful_attempts = [a for a in result['connection_attempts'] if a['success']]
    if successful_attempts:
        result['overall_status'] = 'success'
        result['recommended_config'] = successful_attempts[0]['method']
    else:
        result['overall_status'] = 'failed'
        result['message'] = 'All connection attempts failed'
    
    return jsonify(result)

# Replace the process_document function with this updated version:

@app.route('/process-document', methods=['POST', 'OPTIONS'])
@app.route('/process-document', methods=['POST', 'OPTIONS'])
def process_document():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
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
    global DATABASE_URL, DATABASE_FILE
    
    try:
        if DATABASE_URL:
            # Try to use external PostgreSQL database (persistent)
            try:
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 not available")
                
                # Enhanced connection with better error handling for Supabase
                print(f"🔗 Attempting to connect to database: {DATABASE_URL[:50]}...")
                
                # Parse connection parameters for better debugging
                if 'supabase.co' in DATABASE_URL:
                    print("🟡 Detected Supabase database - using optimized connection settings")
                    # Supabase-specific connection with shorter timeout and better error handling
                    try:
                        conn = psycopg2.connect(
                            DATABASE_URL, 
                            sslmode='require',
                            connect_timeout=15,
                            application_name='rxnorm-portal',
                            target_session_attrs='read-write'
                        )
                        print("✅ Supabase connection established successfully")
                    except psycopg2.OperationalError as op_error:
                        print(f"❌ Supabase connection failed (Operational): {op_error}")
                        # Try alternative connection parameters
                        print("🔄 Trying alternative connection method...")
                        conn = psycopg2.connect(
                            DATABASE_URL, 
                            sslmode='prefer',
                            connect_timeout=30
                        )
                else:
                    # Standard PostgreSQL connection
                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                
                # Test the connection
                cursor = conn.cursor()
                cursor.execute('SELECT version();')
                db_version = cursor.fetchone()[0]
                print(f"✅ Database connected successfully: {db_version[:50]}...")
                
                # Create users table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        assigned_folder VARCHAR(10),
                        assignment_order INTEGER
                    )
                ''')
                print("✅ Connected to external PostgreSQL database")
                
                # Check if assigned_folder column exists
                cursor.execute('''
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='assigned_folder'
                ''')
                if not cursor.fetchone():
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN assigned_folder VARCHAR(10)')
                        print("✅ Added assigned_folder column")
                    except Exception as e:
                        print(f"⚠️ Error adding assigned_folder column: {e}")
                        
                # Create default admin user if no users exist
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                
                if user_count == 0:
                    cursor.execute('''
                        INSERT INTO users (username, email, password, name, registered_at)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', ('admin', 'admin@rxnorm.com', 'admin123', 'System Administrator', datetime.now()))
                    print("✅ Created default admin user")
                
                conn.commit()
                conn.close()
                print(f"✅ Database initialized with {user_count + (1 if user_count == 0 else 0)} users")
                return  # Exit early after successful PostgreSQL initialization
                
            except Exception as pg_error:
                print(f"❌ PostgreSQL connection failed: {pg_error}")
                print(f"🔍 Error type: {type(pg_error).__name__}")
                print(f"🔍 Full error details: {str(pg_error)}")
                
                # Check for specific error types
                if "Network is unreachable" in str(pg_error):
                    print("🌐 Network connectivity issue - Supabase may be unreachable")
                elif "authentication failed" in str(pg_error).lower():
                    print("🔑 Authentication issue - check username/password")
                elif "timeout" in str(pg_error).lower():
                    print("⏰ Connection timeout - try increasing timeout or check network")
                elif "connection refused" in str(pg_error).lower():
                    print("🚫 Connection refused - check if database server is running")
                
                print("🔄 Falling back to SQLite database...")
                DATABASE_URL = None
                DATABASE_FILE = '/tmp/users.db'
                # Continue to SQLite initialization below
        
        if not DATABASE_URL:
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
    """Get database connection (PostgreSQL or SQLite) with improved error handling"""
    global DATABASE_URL, DATABASE_FILE
    
    if DATABASE_URL:
        try:
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("psycopg2 not available")
            
            # Use same connection settings as initialization
            if 'supabase.co' in DATABASE_URL:
                return psycopg2.connect(
                    DATABASE_URL, 
                    sslmode='require',
                    connect_timeout=10,
                    application_name='rxnorm-portal'
                )
            else:
                return psycopg2.connect(DATABASE_URL, sslmode='require')
                
        except Exception as e:
            print(f"❌ PostgreSQL connection failed in get_db_connection: {e}")
            print("🔄 Falling back to SQLite for this operation...")
            DATABASE_URL = None
            DATABASE_FILE = '/tmp/users.db'
            return sqlite3.connect(DATABASE_FILE)
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
        # Use explicit column selection to avoid index issues with schema changes
        result = execute_query('''
            SELECT id, username, email, password, name, registered_at, last_login, assigned_folder, assignment_order
            FROM users WHERE username = ?
        ''', (username,), fetch_one=True)
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'password': result[3],
                'name': result[4],
                'registered_at': result[5],
                'last_login': result[6],
                'assigned_folder': result[7] if len(result) > 7 else None,
                'assignment_order': result[8] if len(result) > 8 else None
            }
        return None
    except Exception as e:
        print(f"⚠️ Error getting user: {e}")
        print(f"🔍 Debug - username: {username}")
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

def get_all_users():
    """List all users (helper function)"""
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
        
        # Create user in database
        if create_user(username, email, password, name):
            print(f"📝 User registered: {username} ({email})")
            
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
            return jsonify({'error': 'Failed to create user - username or email may already exist'}), 409
        
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
        
        # Update last login in database
        update_last_login(username)
        
        print(f"✅ User logged in: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'email': user['email'],
                'name': user['name'],
                'assigned_folder': user.get('assigned_folder')
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

@app.route('/users/folder-assignments', methods=['GET'])
def get_folder_assignments():
    """Debug endpoint to check user folder assignments"""
    try:
        results = execute_query('''
            SELECT username, email, name, assigned_folder, assignment_order, last_login
            FROM users 
            ORDER BY assignment_order ASC
        ''', fetch_all=True)
        
        if not results:
            return jsonify({
                'success': True,
                'assignments': [],
                'message': 'No users found'
            })
        
        assignments = []
        for result in results:
            assignments.append({
                'username': result[0],
                'email': result[1], 
                'name': result[2],
                'assigned_folder': result[3],
                'assignment_order': result[4],
                'last_login': result[5]
            })
        
        # Also provide folder distribution stats
        folder_counts = {}
        for assignment in assignments:
            folder = assignment['assigned_folder']
            if folder:
                folder_counts[folder] = folder_counts.get(folder, 0) + 1
        
        return jsonify({
            'success': True,
            'assignments': assignments,
            'total_users': len(assignments),
            'folder_distribution': folder_counts,
            'expected_folders': list(range(1, 91))  # Should be 1-90
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
        user_list = get_all_users()
        
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
        all_users = get_all_users()
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
def get_admin_folder_assignments():
    """Get folder assignments for admin dashboard"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        # Get all users from database
        users = get_all_users()
        
        # Available folders (9 folders as mentioned in admin.html)
        available_folders = ['100-200', '200-300', '300-400', '400-500', '500-600', '600-700', '700-800', '800-900', '900-1000']
        
        # Assign folders based on registration order (cycle through 9 folders)
        assignments = []
        folder_distribution = {}
        
        for folder in available_folders:
            folder_distribution[folder] = 0
        
        for i, user in enumerate(users):
            # Assign folder based on order (cycle through 9 folders)
            assigned_folder = available_folders[i % len(available_folders)]
            folder_distribution[assigned_folder] += 1
            
            assignments.append({
                'assignment_order': i + 1,
                'name': user.get('name', 'N/A'),
                'email': user.get('email', 'N/A'),
                'assigned_folder': assigned_folder,
                'login_timestamp': user.get('registered_at'),
                'last_login': user.get('last_login')
            })
        
        return jsonify({
            'success': True,
            'assignments': assignments,
            'folder_distribution': folder_distribution,
            'available_folders': available_folders,
            'total_users': len(users)
        })
        
    except Exception as e:
        print(f"❌ Error getting folder assignments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/emails', methods=['GET', 'OPTIONS'])
def get_all_emails():
    """Get all email addresses from the database"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        # Get all users from database
        users = get_all_users()
        
        # Extract just the email addresses
        emails = [user.get('email') for user in users if user.get('email')]
        
        return jsonify({
            'success': True,
            'emails': emails,
            'total_count': len(emails),
            'message': f'Retrieved {len(emails)} email addresses from rxnorm-users database'
        })
        
    except Exception as e:
        print(f"❌ Error getting emails: {e}")
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
    
    # Debug database connection
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"🔗 DATABASE_URL found: {database_url[:50]}...")
        print("📊 Using PostgreSQL database")
    else:
        print("⚠️ No DATABASE_URL found, using SQLite")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
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