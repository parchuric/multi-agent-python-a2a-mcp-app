import os
from app.agents.base_agent import BaseAgent

class HealthAgent(BaseAgent):
    """Agent specialized in health and wellness information."""
    
    def __init__(self, llm, system_message, name="HealthAgent", a2a_handler=None, mcp_handler=None):
        super().__init__(llm, system_message, name, a2a_handler, mcp_handler)
        self.api_key = os.environ.get("HEALTH_API_KEY")
    
    async def process_query(self, query: str) -> str:
        """Process health-related query."""
        prompt = f"""
        You are a health and wellness advisor. Answer the following query:
        
        QUERY: {query}
        
        Provide helpful, accurate information about health topics.
        
        Important disclaimers:
        - You are not a licensed medical professional
        - Your advice does not replace professional medical consultation
        - For medical emergencies, users should contact emergency services
        - Always recommend consulting with healthcare providers for specific medical concerns
        """
        
        return await self.process(prompt)