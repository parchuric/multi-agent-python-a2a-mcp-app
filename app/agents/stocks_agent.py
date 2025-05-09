import os
import re
import json
import httpx  # Add this import
import logging
import requests
from dotenv import load_dotenv
from app.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class StocksAgent(BaseAgent):
    """Agent specialized in financial information."""
    
    def __init__(self, name="StocksAgent", llm=None, a2a_handler=None, mcp_handler=None, 
                 system_message="You are a financial expert that specializes in stock market data and analysis.", **kwargs):
        """Initialize the StocksAgent with the necessary components.
        
        Args:
            name: Name of the agent
            llm: Language model to use
            a2a_handler: Agent-to-agent communication handler
            mcp_handler: Model context protocol handler
            system_message: The system prompt for the agent
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            name=name, 
            llm=llm, 
            a2a_handler=a2a_handler, 
            mcp_handler=mcp_handler,
            system_message=system_message,
            **kwargs
        )
        self.api_key = os.getenv("STOCKS_API_KEY")
        logger.info(f"Stocks API key loaded: {'Yes' if self.api_key else 'No'}")
        
    def _extract_symbols(self, query: str) -> list:
        """Extract potential stock symbols from the query."""
        # Simple regex to find potential stock symbols (1-5 uppercase letters)
        symbols = re.findall(r'\b[A-Z]{1,5}\b', query)
        
        # Common words that might be mistaken for symbols
        common_words = {"I", "A", "THE", "FOR", "AND", "OR", "IF", "IS", "ARE", "TO", "IN"}
        symbols = [s for s in symbols if s not in common_words]
        
        return symbols

    async def get_stock_data(self, symbol: str) -> dict:
        """Get current stock data for a given symbol."""
        try:
            logger.info(f"Fetching stock data for {symbol}")
            
            # Check if API key is available
            if not self.api_key:
                logger.error("Stocks API key not found")
                return {"error": "API key not configured"}
                
            # Alpha Vantage API for real-time stock data
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                data = response.json()
                
            # Check for error responses
            if "Error Message" in data:
                logger.error(f"API Error: {data['Error Message']}")
                return {"error": data["Error Message"]}
                
            if "Global Quote" not in data or not data["Global Quote"]:
                logger.error(f"No data returned for symbol {symbol}")
                return {"error": f"No data available for {symbol}"}
                
            logger.info(f"API test successful: {data['Global Quote']}")
            return data["Global Quote"]
            
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            return {"error": f"Failed to retrieve stock data: {str(e)}"}
    
    async def test_api_connection(self):
        """Test connection to the stock API."""
        test_symbol = "MSFT"
        data = await self.get_stock_data(test_symbol)
        if data and "error" not in data:
            logger.info(f"API test successful: {data}")
            return True
        else:
            logger.warning(f"API test failed: {data}")
            return False

    async def process(self, query: str) -> str:
        """Process a finance-related query."""
        # Extract stock symbols mentioned in the query using regex
        # Matches stock tickers which are typically 1-5 uppercase letters
        symbols = re.findall(r'\b[A-Z]{1,5}\b', query)
        
        # Find common company names and map to their ticker symbols
        common_companies = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "google": "GOOGL",
            "facebook": "META",
            "meta": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            # Add more common companies
        }
        
        # Check query for company names
        query_lower = query.lower()
        for company, ticker in common_companies.items():
            if company in query_lower and ticker not in symbols:
                symbols.append(ticker)
        
        # If no symbols found, extract from query using LLM
        if not symbols:
            extract_prompt = f"""
            Extract potential stock ticker symbols or company names from this query:
            "{query}"
            
            Return only the stock ticker symbol (e.g., AAPL, MSFT) with no additional text.
            If multiple symbols, return the most relevant one.
            If no clear stock or company is mentioned, return "NONE".
            """
            
            extracted_symbol = await super().process(extract_prompt)
            extracted_symbol = extracted_symbol.strip()
            if extracted_symbol and extracted_symbol != "NONE":
                symbols = [extracted_symbol]
        
        # Limit to 3 symbols to avoid overloading
        symbols = symbols[:3]
        
        # If still no symbols, provide a general response
        if not symbols:
            return "I don't see any specific stock symbols in your query. Please mention a specific company or stock symbol like AAPL for Apple or MSFT for Microsoft."
        
        # Get stock data for each symbol
        stock_data = {}
        for symbol in symbols:
            stock_data[symbol] = await self.get_stock_data(symbol)
        
        # Format the stock data results for the prompt
        formatted_data = []
        for symbol, data in stock_data.items():
            if "error" in data:
                formatted_data.append(f"{symbol}: Error - {data['error']}")
            else:
                formatted_data.append(f"{symbol}:\n" + "\n".join([f"- {k}: {v}" for k, v in data.items()]))
        
        stock_info = "\n\n".join(formatted_data)
        
        # Generate response using LLM
        prompt = f"""
        Query: {query}
        
        Stock Data:
        {stock_info}
        
        Based on the stock data above, provide a clear and informative response to the query.
        Include relevant price information, percentage changes, and any notable context.
        If there was an error retrieving data, acknowledge it and provide general information if possible.
        """
        
        # Use the base agent's process method to generate a response
        return await super().process(prompt)

    # Add this method to your StocksAgent class
    async def process_query(self, query: str) -> str:
        """Alias for the process method to maintain compatibility."""
        # Simply call the process method
        return await self.process(query)