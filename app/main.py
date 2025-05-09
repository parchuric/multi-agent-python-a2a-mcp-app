import os
import sys
import asyncio
import threading
import logging
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.router_agent import RouterAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.sports_agent import SportsAgent
from app.agents.news_agent import NewsAgent
from app.agents.stocks_agent import StocksAgent
from app.agents.health_agent import HealthAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.synthesizer_agent import SynthesizerAgent
from app.chains.langgraph_chain import MultiAgentLangGraph
from app.prompts.prompt_templates import (
    ANALYZER_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    WEATHER_SYSTEM_PROMPT,
    SPORTS_SYSTEM_PROMPT,
    NEWS_SYSTEM_PROMPT,
    STOCKS_SYSTEM_PROMPT,
    HEALTH_SYSTEM_PROMPT,
    EVALUATOR_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT
)
from app.utils.a2a_protocol import A2AProtocolHandler
from app.utils.mcp_protocol import MCPHandler
from app.api.server import init_app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for Azure OpenAI API credentials
azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID")

if not all([azure_api_key, azure_endpoint, azure_deployment]):
    logger.error("Azure OpenAI credentials not found!")
    print("ERROR: Azure OpenAI credentials not found!")
    print("Please ensure your .env file contains the following variables:")
    print("AZURE_OPENAI_API_KEY=your_api_key_here")
    print("AZURE_OPENAI_ENDPOINT=your_endpoint_here")
    print("AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id_here")
    sys.exit(1)

async def init_langgraph():
    """Initialize the LangGraph system."""
    try:
        logger.info("Initializing Azure OpenAI LLM...")
        
        # Find where your LLM is initialized and add this:
        deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")
        logger.info(f"Using Azure OpenAI deployment ID: {deployment_id}")

        llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2023-05-15",  # Adjust if needed
            temperature=0.2
        )
        
        logger.info("Initializing A2A and MCP handlers...")
        a2a_handler = A2AProtocolHandler()
        mcp_handler = MCPHandler()
        
        logger.info("Initializing specialized agents...")
        # Initialize all specialized agents
        analyzer = AnalyzerAgent(llm, ANALYZER_SYSTEM_PROMPT, "Analyzer", a2a_handler, mcp_handler)
        router = RouterAgent(llm, ROUTER_SYSTEM_PROMPT, "Router", a2a_handler, mcp_handler)
        weather_agent = WeatherAgent(llm, WEATHER_SYSTEM_PROMPT, "WeatherAgent", a2a_handler, mcp_handler)
        sports_agent = SportsAgent(llm, SPORTS_SYSTEM_PROMPT, "SportsAgent", a2a_handler, mcp_handler)
        news_agent = NewsAgent(llm, NEWS_SYSTEM_PROMPT, "NewsAgent", a2a_handler, mcp_handler)
        stocks_agent = StocksAgent(llm, STOCKS_SYSTEM_PROMPT, "StocksAgent", a2a_handler, mcp_handler)
        health_agent = HealthAgent(llm, HEALTH_SYSTEM_PROMPT, "HealthAgent", a2a_handler, mcp_handler)
        evaluator = EvaluatorAgent(llm, EVALUATOR_SYSTEM_PROMPT, "Evaluator", a2a_handler, mcp_handler)
        synthesizer = SynthesizerAgent(llm, SYNTHESIZER_SYSTEM_PROMPT, "Synthesizer", a2a_handler, mcp_handler)
        
        # Add this after initializing your agents
        logger.info("Testing API connections...")
        if news_agent.api_key:
            if news_agent.test_api_connection():
                logger.info("News API connection successful")
            else:
                logger.warning("News API connection failed - check API key and limits")

        if stocks_agent.api_key:
            if stocks_agent.test_api_connection():
                logger.info("Stocks API connection successful")
            else:
                logger.warning("Stocks API connection failed - check API key and limits")
        
        # Create LangGraph workflow
        logger.info("Building LangGraph workflow...")
        graph = MultiAgentLangGraph(
            analyzer, router, weather_agent, sports_agent, news_agent,
            stocks_agent, health_agent, evaluator, synthesizer,
            a2a_handler, mcp_handler,
            recursion_limit=3  # Add this parameter
        )
        
        logger.info("LangGraph initialization complete!")
        return graph
        
    except Exception as e:
        logger.error(f"Error initializing LangGraph: {e}")
        raise

def start_api_server(graph):
    """Start the Flask API server in a separate thread."""
    logger.info("Starting API server...")
    init_app(graph)

async def test_query(graph):
    """Test the system with a sample query."""
    test_queries = [
        "What's the weather like in Seattle today?",
        "Who won the latest NBA championship?",
        "What are the latest headlines about AI technology?",
        "How is Apple stock performing this week?",
        "What are some tips for reducing stress and anxiety?"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: {query}")
        result = await graph.process_query(query)
        print(f"\n==== Query: {query} ====\n")
        print(f"Topic: {result['topic']}")
        print(f"Agents consulted: {result['agents_consulted']}")
        print(f"Response: {result['response']}")
        print("\n" + "="*50 + "\n")

async def main():
    """Main entry point for the application."""
    try:
        # Initialize LangGraph
        graph = await init_langgraph()
        
        # Start API server in a separate thread
        api_thread = threading.Thread(target=start_api_server, args=(graph,), daemon=True)
        api_thread.start()
        
        # Optionally run test queries
        await test_query(graph)
        
        # Keep the main thread alive
        while api_thread.is_alive():
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())