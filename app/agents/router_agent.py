from app.agents.base_agent import BaseAgent
from typing import List

class RouterAgent(BaseAgent):
    """Agent that routes queries to the appropriate specialized agents."""
    
    async def route_query(self, query: str, topic: str) -> List[str]:
        """Determine which specialized agents should handle the query."""
        prompt = f"""
        You are an expert router that determines which specialized agents should handle a user query.
        Based on the query and identified topic, select the appropriate agent(s).
        
        USER QUERY: {query}
        IDENTIFIED TOPIC: {topic}
        
        Available agents:
        - WeatherAgent: Handles weather-related queries
        - SportsAgent: Processes sports-related information
        - NewsAgent: Provides current events information
        - StocksAgent: Delivers financial market data
        - HealthAgent: Answers health and wellness questions
        
        You can select one primary agent or multiple agents if the query touches multiple domains.
        Respond with only the agent names, separated by commas (e.g., "WeatherAgent" or "NewsAgent,StocksAgent").
        """
        
        response = await self.process(prompt)
        # Parse the response into a list of agent names
        agents = [name.strip() for name in response.split(",")]
        
        # Map topic to default agent if response isn't clear
        default_agents = {
            "weather": ["WeatherAgent"],
            "sports": ["SportsAgent"],
            "news": ["NewsAgent"],
            "stocks": ["StocksAgent"],
            "health": ["HealthAgent"],
            "general": ["NewsAgent"]  # Default to news for general queries
        }
        
        # Validate agent names and use defaults if necessary
        valid_agent_names = ["WeatherAgent", "SportsAgent", "NewsAgent", "StocksAgent", "HealthAgent"]
        valid_agents = [agent for agent in agents if agent in valid_agent_names]
        
        if not valid_agents:
            valid_agents = default_agents.get(topic, ["NewsAgent"])
            
        return valid_agents