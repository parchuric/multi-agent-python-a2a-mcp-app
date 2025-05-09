import os
import re
import json
import logging
import requests
from dotenv import load_dotenv
from app.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class StocksAgent(BaseAgent):
    """Agent specialized in retrieving and answering finance and stock-related queries."""
    
    def __init__(self, llm=None, system_prompt=None, name=None, a2a_handler=None, mcp_handler=None):
        """Initialize the StocksAgent.
        
        Args:
            llm: Language model to use
            system_prompt: System prompt for the agent
            name: Name of the agent
            a2a_handler: Agent-to-agent protocol handler
            mcp_handler: Multi-context protocol handler
        """
        super().__init__(llm, system_prompt, name, a2a_handler, mcp_handler)
        # Get API key from environment
        self.api_key = os.getenv("STOCKS_API_KEY")
        logger.info(f"Stocks API key loaded: {'Yes' if self.api_key else 'No'}")
        
    async def process_query(self, query: str) -> str:
        """Process finance-related query."""
        # Extract potential stock symbols from query
        symbols = self._extract_symbols(query)
        stock_data = {}
        
        if symbols:
            for symbol in symbols[:3]:  # Limit to 3 symbols to avoid API limits
                stock_data[symbol] = self._fetch_stock_data(symbol)
        
        # Generate prompt based on available data
        if stock_data and not all("error" in (data if isinstance(data, dict) else {}) for symbol, data in stock_data.items()):
            stock_info = json.dumps(stock_data, indent=2)
            prompt = f"""
            You are a financial expert. Answer the following query about stocks or financial markets:
            
            QUERY: {query}
            
            STOCK DATA: {stock_info}
            
            Based on this data, provide a helpful and informative response.
            If the stock data shows an error for some symbols, focus on the available data
            and provide general information about the stocks with errors.
            """
        else:
            prompt = f"""
            You are a financial expert. Answer the following query about stocks or financial markets:
            
            QUERY: {query}
            
            NOTE: I don't have access to real-time stock data for the symbols mentioned. 
            Provide general information about the stocks or financial topics in the query,
            and suggest reliable sources where the user can find up-to-date information.
            """
        
        return await self.process(prompt)
    
    def _extract_symbols(self, query: str) -> list:
        """Extract potential stock symbols from the query."""
        # Simple regex to find potential stock symbols (1-5 uppercase letters)
        symbols = re.findall(r'\b[A-Z]{1,5}\b', query)
        
        # Common words that might be mistaken for symbols
        common_words = {"I", "A", "THE", "FOR", "AND", "OR", "IF", "IS", "ARE", "TO", "IN"}
        symbols = [s for s in symbols if s not in common_words]
        
        return symbols

    def _fetch_stock_data(self, symbol: str) -> dict:
        """Fetch stock data from Alpha Vantage API."""
        if not self.api_key:
            logger.warning("Stock API key not available")
            return {"error": "API key not configured"}
        
        try:
            # Alpha Vantage API endpoint for global quote (current price data)
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            logger.info(f"Fetching stock data for {symbol}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Global Quote" in data and data["Global Quote"]:
                    return data["Global Quote"]
                elif "Note" in data:
                    # API limit reached
                    logger.warning(f"API limit issue: {data['Note']}")
                    return {"error": "API request limit reached"}
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return {"error": "Unexpected API response format"}
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            return {"error": f"Failed to retrieve stock data: {str(e)}"}
    
    def test_api_connection(self):
        """Test connection to the stock API."""
        test_symbol = "MSFT"
        data = self._fetch_stock_data(test_symbol)
        if data and "error" not in data:
            logger.info(f"API test successful: {data}")
            return True
        else:
            logger.warning(f"API test failed: {data}")
            return False