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

try:
    from app.utils.token_counter import TokenCounterMiddleware
    USE_TOKEN_COUNTER = True
except ImportError:
    print("Token counter not available, proceeding without token counting")
    USE_TOKEN_COUNTER = False

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

        azure_llm = AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
            openai_api_version="2023-05-15",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )

        if USE_TOKEN_COUNTER:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Wrap the LLM with token counter
            azure_llm = TokenCounterMiddleware(azure_llm, log_file="logs/token_usage.json")
        
        logger.info("Initializing A2A and MCP handlers...")
        a2a_handler = A2AProtocolHandler()
        mcp_handler = MCPHandler()
        
        logger.info("Initializing specialized agents...")
        # Initialize all specialized agents
        analyzer = AnalyzerAgent(azure_llm, ANALYZER_SYSTEM_PROMPT, "Analyzer", a2a_handler, mcp_handler)
        router = RouterAgent(azure_llm, ROUTER_SYSTEM_PROMPT, "Router", a2a_handler, mcp_handler)
        weather_agent = WeatherAgent(azure_llm, WEATHER_SYSTEM_PROMPT, "WeatherAgent", a2a_handler, mcp_handler)
        sports_agent = SportsAgent(azure_llm, SPORTS_SYSTEM_PROMPT, "SportsAgent", a2a_handler, mcp_handler)
        news_agent = NewsAgent(azure_llm, NEWS_SYSTEM_PROMPT, "NewsAgent", a2a_handler, mcp_handler)
        stocks_agent = StocksAgent(
            name="StocksAgent", 
            llm=azure_llm, 
            a2a_handler=a2a_handler, 
            mcp_handler=mcp_handler
            # Remove the memory parameter
        )
        health_agent = HealthAgent(azure_llm, HEALTH_SYSTEM_PROMPT, "HealthAgent", a2a_handler, mcp_handler)
        evaluator = EvaluatorAgent(azure_llm, EVALUATOR_SYSTEM_PROMPT, "Evaluator", a2a_handler, mcp_handler)
        synthesizer = SynthesizerAgent(azure_llm, SYNTHESIZER_SYSTEM_PROMPT, "Synthesizer", a2a_handler, mcp_handler)
        
        # Add this after initializing your agents
        logger.info("Testing API connections...")
        if news_agent.api_key:
            if news_agent.test_api_connection():
                logger.info("News API connection successful")
            else:
                logger.warning("News API connection failed - check API key and limits")

        if stocks_agent.api_key:
            if await stocks_agent.test_api_connection():
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
        
        if USE_TOKEN_COUNTER:
            # Add token counter to graph for access from API
            graph.token_counter = azure_llm
        
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
    # Test a single query in debug mode with full error handling
    try:
        test_query = "What's the weather like in Seattle today?"
        logger.info(f"Testing query: {test_query}")
        
        response = await graph.process_query(test_query)
        print(f"\n==== Query: {test_query} ====\n")
        # Handle either string or dictionary response format
        if isinstance(response, dict):
            print(f"Topic: {response.get('topic', 'N/A')}")
            print(f"Agents consulted: {response.get('agents_consulted', 'N/A')}")
            print(f"Response: {response.get('response', 'No response available')}")
        else:
            # It's a string response
            print(response)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Only run the other queries if you want to test them
    test_other_queries = False
    if test_other_queries:
        test_queries = [
            "Who won the latest NBA championship?",
            "What are the latest headlines about AI technology?",
            "How is Apple stock performing this week?",
            "What are some tips for reducing stress and anxiety?"
        ]
        
        for query in test_queries:
            try:
                logger.info(f"Testing query: {query}")
                result = await graph.process_query(query)
                print(f"\n==== Query: {query} ====\n")
                
                # Handle either string or dictionary response format
                if isinstance(result, dict):
                    print(f"Topic: {result.get('topic', 'N/A')}")
                    print(f"Agents consulted: {result.get('agents_consulted', 'N/A')}")
                    print(f"Response: {result.get('response', 'No response available')}")
                else:
                    # It's a string response
                    print(result)
                print("\n" + "="*50 + "\n")
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")

async def test_stock_agent(graph):
    """Test the stock agent specifically."""
    try:
        test_query = "How is Microsoft stock performing today?"
        logger.info(f"Testing stock agent with query: {test_query}")
        
        # Set up state that directly uses the stock agent
        initial_state = {
            "user_query": test_query,
            "selected_agents": ["StocksAgent"],
            "conversation_history": [],
            "metadata": {
                "thread_id": str(uuid.uuid4())
            }
        }
        
        # Process directly with the specialized agent node
        stocks_agent = next((agent for agent in graph.specialized_agents 
                           if agent.name == "StocksAgent"), None)
        
        if not stocks_agent:
            logger.error("StocksAgent not found in specialized agents")
            return
            
        # Test API key is loaded
        logger.info(f"Stock Agent API Key: {'Present' if stocks_agent.api_key else 'Missing'}")
        
        # Test stock data retrieval directly
        msft_data = await stocks_agent.get_stock_data("MSFT")
        logger.info(f"Direct MSFT data test: {msft_data}")
        
        # Test full processing
        response = await stocks_agent.process(test_query)
        logger.info(f"StocksAgent response: {response}")
        
        print(f"\n==== Stock Agent Test: {test_query} ====\n")
        print(response)
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Error testing stock agent: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def generate_token_usage_report(token_counter):
    """Generate a comprehensive token usage report."""
    total_usage = token_counter.get_total_usage()
    agent_usage = token_counter.get_usage_by_agent()
    
    # Calculate costs (approximate)
    input_cost_per_1k = 0.003  # Azure GPT-4 input cost per 1K tokens
    output_cost_per_1k = 0.006  # Azure GPT-4 output cost per 1K tokens
    
    prompt_cost = total_usage["prompt_tokens"] * input_cost_per_1k / 1000
    completion_cost = total_usage["completion_tokens"] * output_cost_per_1k / 1000
    total_cost = prompt_cost + completion_cost
    
    # Format the report
    report = [
        "==== Token Usage Report ====",
        f"Total API Calls: {total_usage['call_count']}",
        f"Total Prompt Tokens: {total_usage['prompt_tokens']}",
        f"Total Completion Tokens: {total_usage['completion_tokens']}",
        f"Total Tokens: {total_usage['total_tokens']}",
        f"Estimated Cost: ${total_cost:.4f} (${prompt_cost:.4f} input + ${completion_cost:.4f} output)",
        "\n==== Usage by Agent ===="
    ]
    
    for agent, usage in agent_usage.items():
        agent_prompt_cost = usage["prompt_tokens"] * input_cost_per_1k / 1000
        agent_completion_cost = usage["completion_tokens"] * output_cost_per_1k / 1000
        agent_total_cost = agent_prompt_cost + agent_completion_cost
        
        report.append(f"\nAgent: {agent}")
        report.append(f"  API Calls: {usage['call_count']}")
        report.append(f"  Prompt Tokens: {usage['prompt_tokens']}")
        report.append(f"  Completion Tokens: {usage['completion_tokens']}")
        report.append(f"  Total Tokens: {usage['total_tokens']}")
        report.append(f"  Estimated Cost: ${agent_total_cost:.4f}")
    
    return "\n".join(report)

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