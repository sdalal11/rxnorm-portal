from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import subprocess
import json

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
        'version': '1.0',
        'endpoints': {
            'health': '/health',
            'process': '/process-document'
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
# Global configuration storage (in production, use a database)
global_config = {}

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

                'confidence': 0.7,
                'source': 'main.py',
                'rxnorm_code': None
            })
    
    return annotations

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