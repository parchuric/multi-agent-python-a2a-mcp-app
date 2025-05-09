from flask import Flask, request, jsonify, send_from_directory  # type: ignore
from flask_cors import CORS
import asyncio
import os
import logging
from app.chains.langgraph_chain import MultiAgentLangGraph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the directory of the static files
static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

# Initialize Flask app
app = Flask(__name__, static_folder=static_folder)
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
        return jsonify({"error": "System not initialized"}), 500
    
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400
    
    query = data['query']
    logger.info(f"Received query: {query}")
    
    # Run the async process in a synchronous context
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(graph.process_query(query))
        loop.close()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            "error": str(e),
            "query": query,
            "response": "Sorry, I encountered an error while processing your query."
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "message": "System is running"})

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