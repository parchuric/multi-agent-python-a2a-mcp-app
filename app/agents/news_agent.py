import os
import logging
import requests
from dotenv import load_dotenv
from app.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NewsAgent(BaseAgent):
    """Agent specialized in retrieving and answering news-related queries."""
    
    def __init__(self, llm=None, system_prompt=None, name=None, a2a_handler=None, mcp_handler=None):
        """Initialize the NewsAgent.
        
        Args:
            llm: Language model to use
            system_prompt: System prompt for the agent
            name: Name of the agent
            a2a_handler: Agent-to-agent protocol handler
            mcp_handler: Multi-context protocol handler
        """
        super().__init__(llm, system_prompt, name, a2a_handler, mcp_handler)
        # Get API key from environment
        self.api_key = os.getenv("NEWS_API_KEY")
        logger.info(f"News API key loaded: {'Yes' if self.api_key else 'No'}")
        
    async def process_query(self, query: str, keywords: str = None) -> str:
        """Process news-related query."""
        news_data = None
        
        try:
            if self.api_key:
                try:
                    news_data = self._fetch_news_data(keywords or query)
                except Exception as e:
                    logger.error(f"Error fetching news data: {e}")
        except Exception as e:
            logger.error(f"General error in news agent: {e}")
        
        if news_data:
            prompt = f"""
            You are a news expert. Answer the following query about current events:
            
            QUERY: {query}
            
            NEWS DATA: {news_data}
            
            Provide an accurate, up-to-date response about the news topic.
            If the news data doesn't fully address the query, synthesize what you know about the topic
            to give the most helpful response possible.
            """
        else:
            prompt = f"""
            You are a news expert. Answer the following query about current events:
            
            QUERY: {query}
            
            NOTE: I don't have access to the latest news data, but I'll provide the most helpful information I can
            based on my general knowledge.
            
            Provide a helpful response about the topic, making it clear that you're providing general information
            rather than the latest headlines. Focus on general trends and well-established facts about the topic.
            """
        
        return await self.process(prompt)

    def _fetch_news_data(self, query: str) -> dict:
        """Fetch news data from NewsAPI."""
        if not self.api_key:
            logger.warning("News API key not available")
            return None
            
        try:
            # NewsAPI implementation
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "apiKey": self.api_key,
                    "q": query,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 5
                },
                timeout=5  # Add timeout to prevent hanging
            )
            
            if response.status_code == 200:
                data = response.json()
                # Simplify the response for LLM consumption
                articles = []
                for article in data.get("articles", [])[:3]:  # Limit to first 3 articles
                    articles.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "published": article.get("publishedAt"),
                        "description": article.get("description"),
                        "url": article.get("url")
                    })
                return articles
            else:
                logger.error(f"Error fetching news: {response.status_code}")
                return [{"error": f"Could not retrieve news: Status code {response.status_code}"}]
        except Exception as e:
            logger.error(f"News API error: {e}")
            return [{"error": f"Could not retrieve news: {str(e)}"}]
    
    def test_api_connection(self):
        """Test connection to the news API."""
        test_query = "technology"
        data = self._fetch_news_data(test_query)
        if data and not any("error" in (item if isinstance(item, dict) else {}) for item in data):
            logger.info(f"News API test successful: {len(data)} articles retrieved")
            return True
        else:
            logger.warning(f"News API test failed")
            return False