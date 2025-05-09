import os
import requests
from app.agents.base_agent import BaseAgent

class SportsAgent(BaseAgent):
    """Agent specialized in sports-related information."""
    
    def __init__(self, llm, system_message, name="SportsAgent", a2a_handler=None, mcp_handler=None):
        super().__init__(llm, system_message, name, a2a_handler, mcp_handler)
        self.api_key = os.environ.get("SPORTS_API_KEY")
    
    async def process_query(self, query: str, sport: str = None, team: str = None) -> str:
        """Process sports-related query."""
        sports_data = None
        if self.api_key and (sport or team):
            try:
                sports_data = self._fetch_sports_data(sport, team)
            except Exception as e:
                self.add_message_to_history("system", f"Error fetching sports data: {e}")
        
        prompt = f"""
        You are a sports expert. Answer the following query:
        
        QUERY: {query}
        
        {f'SPORTS DATA: {sports_data}' if sports_data else ''}
        
        Provide an accurate, informative response about sports information.
        If no sports data is available, provide general information but be clear about the limitations.
        """
        
        return await self.process(prompt)
    
    def _fetch_sports_data(self, sport: str = None, team: str = None) -> dict:
        """Fetch sports data from an external API."""
        # Placeholder for actual API implementation
        if not self.api_key:
            return None
            
        # This would be replaced with actual API call
        return {"message": "Sports data API not implemented"}