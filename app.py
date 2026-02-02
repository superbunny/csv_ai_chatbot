"""
Flask backend for CSV Chatbot with Gemini AI integration.
Provides API endpoints for file upload, chat, and visualizations.
"""

from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from werkzeug.utils import secure_filename
from tools import DataFrameAnalyzer, TOOLS
import uuid

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('visualizations', exist_ok=True)

# Store DataFrames and chat history per session
# In production, use Redis or database
sessions_data = {}


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_id():
    """Get or create session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a CSV file'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Read CSV into DataFrame
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            return jsonify({'error': f'Error reading CSV: {str(e)}'}), 400
        
        # Initialize session data
        session_id = get_session_id()
        analyzer = DataFrameAnalyzer(df)
        
        sessions_data[session_id] = {
            'df': df,
            'analyzer': analyzer,
            'filename': filename,
            'filepath': filepath,
            'chat_history': []
        }
        
        # Get basic info
        info = analyzer.dataframe_info()
        
        
        # Get preview data (first 100 rows for pagination)
        preview_data = df.head(100).to_dict('records')
        
        # Clean NaN values from dict (to_dict converts None back to nan)
        import math
        for row in preview_data:
            for key in list(row.keys()):
                value = row[key]
                # Check if value is float NaN
                if isinstance(value, float) and math.isnan(value):
                    row[key] = None
        
        columns = list(df.columns)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'info': info,
            'preview': {
                'columns': columns,
                'rows': preview_data
            },
            'message': f'Successfully uploaded {filename} with {info["shape"]["rows"]} rows and {info["shape"]["columns"]} columns'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests with Gemini AI."""
    import json
    from google.generativeai import protos
    import google.ai.generativelanguage as glm
    
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        session_id = get_session_id()
        
        # Check if session has data
        if session_id not in sessions_data:
            return jsonify({'error': 'No CSV file uploaded. Please upload a file first.'}), 400
        
        session_state = sessions_data[session_id]
        analyzer = session_state['analyzer']
        chat_history = session_state['chat_history']
        
        # Add user message to history
        chat_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Create Gemini model with tools  
        # Convert tool definitions to proper FunctionDeclaration format
        
        function_declarations = []
        for tool in TOOLS:
            # Convert parameters dict to Schema
            params_dict = tool['parameters']
            properties = {}
            
            for prop_name, prop_def in params_dict.get('properties', {}).items():
                # Convert property definition to Schema
                prop_type = prop_def.get('type', 'string')
                type_mapping = {
                    'string': protos.Type.STRING,
                    'array': protos.Type.ARRAY,
                    'object': protos.Type.OBJECT,
                    'number': protos.Type.NUMBER,
                    'integer': protos.Type.INTEGER,
                    'boolean': protos.Type.BOOLEAN
                }
                
                # Build Schema kwargs dynamically (only add non-None values)
                prop_schema_kwargs = {
                    'type': type_mapping.get(prop_type, protos.Type.STRING)
                }
                if 'description' in prop_def:
                    prop_schema_kwargs['description'] = prop_def['description']
                if 'enum' in prop_def:
                    prop_schema_kwargs['enum'] = prop_def['enum']
                if 'items' in prop_def:
                    items_type = prop_def['items'].get('type', 'string')
                    prop_schema_kwargs['items'] = protos.Schema(
                        type=type_mapping.get(items_type, protos.Type.STRING)
                    )
                
                properties[prop_name] = protos.Schema(**prop_schema_kwargs)
            
            parameters_schema = protos.Schema(
                type=protos.Type.OBJECT,
                properties=properties,
                required=params_dict.get('required', [])
            )
            
            func_dec = protos.FunctionDeclaration(
                name=tool['name'],
                description=tool['description'],
                parameters=parameters_schema
            )
            function_declarations.append(func_dec)
        
        tool_declarations = [protos.Tool(function_declarations=function_declarations)]
        
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            tools=tool_declarations
        )
        
        # Build conversation history for Gemini in the correct format
        history_for_gemini = []
        
        # Add system context on first message only
        if len(chat_history) == 1:
            df_info = analyzer.dataframe_info()
            system_context = f"""You are a helpful data analyst assistant. The user has uploaded a CSV file named '{session_state['filename']}' with the following structure:
- Rows: {df_info['shape']['rows']}
- Columns: {df_info['shape']['columns']}
- Column names: {', '.join(df_info['columns'])}
- Data types: {json.dumps(df_info['dtypes'], indent=2)}

You have access to analysis tools to help answer questions about this data. Use the appropriate tools to provide accurate, helpful responses. When the user asks follow-up questions, remember the context from previous messages."""
            
            history_for_gemini.append({
                'role': 'user',
                'parts': [system_context]
            })
            history_for_gemini.append({
                'role': 'model',
                'parts': ['I understand. I\'ll help you analyze this CSV data. What would you like to know?']
            })
        
        # Add previous conversation history (exclude current message)
        for msg in chat_history[:-1]:  # All messages except current
            if msg['role'] == 'user':
                history_for_gemini.append({
                    'role': 'user',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'assistant':
                history_for_gemini.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })
        # Send to Gemini with full conversation history
        chat = model.start_chat(history=history_for_gemini)
        response = chat.send_message(user_message)
        
        # Check if Gemini wants to call functions
        function_responses = []
        
        while response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            # Check for function call
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                print(f"DEBUG: Calling function: {function_name} with args: {function_args}")
                
                # Execute the function
                try:
                    if function_name == 'dataframe_info':
                        result = analyzer.dataframe_info()
                    elif function_name == 'statistical_summary':
                        result = analyzer.statistical_summary(**function_args)
                    elif function_name == 'python_analysis':
                        result = analyzer.python_analysis(**function_args)
                    elif function_name == 'create_visualization':
                        result = analyzer.create_visualization(**function_args)
                    else:
                        result = {"error": f"Unknown function: {function_name}"}
                    
                    print(f"DEBUG: Function {function_name} returned: {str(result)[:200]}...")
                except Exception as func_error:
                    print(f"DEBUG: Function {function_name} failed: {func_error}")
                    import traceback
                    traceback.print_exc()
                    result = {"error": f"Function execution failed: {str(func_error)}"}
                
                function_responses.append({
                    'function': function_name,
                    'arguments': function_args,
                    'result': result
                })
                
                # Send function result back to Gemini
                # Convert result to JSON and back to ensure all types are serializable
                # This handles numpy types, integer keys, etc.
                try:
                    json_str = json.dumps(result, default=str)
                    serializable_result = json.loads(json_str)
                except Exception as json_error:
                    print(f"DEBUG: JSON conversion failed: {json_error}, using string conversion")
                    serializable_result = {"data": str(result)}
                
                print(f"DEBUG: Sending serializable result: {str(serializable_result)[:200]}...")
                
                response = chat.send_message(
                    glm.Content(
                        parts=[
                            glm.Part(
                                function_response=glm.FunctionResponse(
                                    name=function_name,
                                    response={"result": serializable_result}
                                )
                            )
                        ]
                    )
                )
            else:
                # No more function calls, get final response
                break
        
        # Extract final text response safely
        try:
            assistant_message = response.text
        except ValueError:
            # If response has no text (e.g., only function calls), get text from parts
            text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text]
            assistant_message = ' '.join(text_parts) if text_parts else "I've processed the data."
        
        # Add assistant response to history
        chat_history.append({
            'role': 'assistant',
            'content': assistant_message,
            'function_calls': function_responses if function_responses else None
        })
        
        # Check if any visualizations were created
        visualizations = []
        for func_resp in function_responses:
            if func_resp['function'] == 'create_visualization' and 'url' in func_resp['result']:
                visualizations.append(func_resp['result']['url'])
        
        return jsonify({
            'success': True,
            'message': assistant_message,
            'function_calls': function_responses,
            'visualizations': visualizations
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CHAT ERROR TRACEBACK:\n{error_trace}")
        return jsonify({'error': f'Chat error: {str(e)}'}), 500


@app.route('/api/viz/<filename>', methods=['GET'])
def get_visualization(filename):
    """Serve visualization images."""
    try:
        filepath = os.path.join('visualizations', secure_filename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/png')
        else:
            return jsonify({'error': 'Visualization not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear current session data."""
    try:
        session_id = get_session_id()
        if session_id in sessions_data:
            del sessions_data[session_id]
        session.clear()
        return jsonify({'success': True, 'message': 'Session cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model': GEMINI_MODEL,
        'active_sessions': len(sessions_data)
    })


@app.route('/')
def index():
    """Serve the main page."""
    return send_file('index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    if os.path.exists(path):
        return send_file(path)
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    print("=" * 60)
    print("CSV Chatbot Backend Server")
    print("=" * 60)
    print(f"Gemini Model: {GEMINI_MODEL}")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print("Server starting on http://localhost:5001")
    print("=" * 60)   
    app.run(debug=True, host='0.0.0.0', port=5001)
