import os
import requests
from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional

class WeatherAgent(BaseAgent):
    """Agent specialized in handling weather-related queries."""
    
    def __init__(self, llm, system_message, name="WeatherAgent", a2a_handler=None, mcp_handler=None):
        super().__init__(llm, system_message, name, a2a_handler, mcp_handler)
        self.api_key = os.environ.get("WEATHER_API_KEY")
    
    async def process_query(self, query: str, location: Optional[str] = None) -> str:
        """Process weather-related query."""
        # If we have an API key, try to get real weather data
        weather_data = None
        if self.api_key and location:
            try:
                weather_data = self._fetch_weather_data(location)
            except Exception as e:
                self.add_message_to_history("system", f"Error fetching weather data: {e}")
        
        # Construct prompt with weather data if available
        prompt = f"""
        You are a weather expert. Answer the following query:
        
        QUERY: {query}
        
        {f'WEATHER DATA: {weather_data}' if weather_data else ''}
        
        Provide an informative, accurate response about weather conditions.
        If no weather data is available, provide general information but be clear about the limitations.
        """
        
        return await self.process(prompt)
    
    def _fetch_weather_data(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from an external API."""
        # This is a placeholder. Implement actual API call based on the weather service you use
        if not self.api_key:
            return None
            
        # Example API call to a weather service
        response = requests.get(
            f"https://api.weatherapi.com/v1/current.json",
            params={
                "key": self.api_key,
                "q": location,
                "aqi": "no"
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching weather data: {response.status_code}")