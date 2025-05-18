from flask import Flask, request, jsonify, send_from_directory, render_template  # type: ignore
from flask_cors import CORS
import asyncio
import os
import logging
from app.chains.langgraph_chain import MultiAgentLangGraph
from app.utils.token_counter import generate_token_usage_report, TokenCounterMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the directory of the static files
static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
# Get the template directory
template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

# Initialize Flask app with template folder
app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
CORS(app)  # Enable CORS for all routes

# Global variable to hold our graph instance
graph = None

@app.route('/')
def index():
    """Serve the index.html file."""
    return send_from_directory(static_folder, 'index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a user query using the multi-agent system."""
    if not graph:
        return jsonify({"error": "Graph not initialized"}), 500
        
    data = request.json
    query = data.get("query", "")
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    try:
        # Process the query asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(graph.process_query(query))
        loop.close()
        
        # If response is a string, convert to simple response object
        if isinstance(response, str):
            return jsonify({"response": response})
            
        # If it's already a dict, ensure it has a response field
        elif isinstance(response, dict):
            # Make a clean copy of the dict to prevent modification issues
            clean_response = {}
            
            # Include only the necessary fields for the UI
            if 'response' in response:
                clean_response['response'] = response['response']
            if 'topic' in response:
                clean_response['topic'] = response['topic']
            if 'agents_consulted' in response:
                clean_response['agents_consulted'] = response['agents_consulted']
                
            # If we don't have a response field, try to determine the main content
            if 'response' not in clean_response:
                clean_response['response'] = response.get('result', str(response))
                
            return jsonify(clean_response)
        
        # Fallback for any other type
        else:
            return jsonify({"response": str(response)})
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        
        # Get detailed error information
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        
        # Convert any error to a string
        error_message = str(e)
        
        # Provide better error messages for common errors
        if "object ChatCompletion can't be used in 'await' expression" in error_message:
            error_message = "API compatibility issue. Please try again."
        elif "conversation_id" in error_message:
            error_message = "Azure OpenAI API version doesn't support this feature. Using fallback mode."
        
        return jsonify({"error": error_message}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "message": "System is running"})

@app.route('/usage-report')
def usage_report():
    """Serve the token usage report."""
    if hasattr(graph, 'token_counter'):
        report = generate_token_usage_report(graph.token_counter)
        return render_template('usage_report.html', report=report)
    return "Token counter not available", 404

def init_app(initialized_graph):
    """Initialize the Flask app with the provided graph."""
    global graph
    graph = initialized_graph
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # This code only runs if the script is executed directly
    logger.warning("This file should not be executed directly. Use main.py instead.")