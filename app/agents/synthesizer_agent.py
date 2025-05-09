from app.agents.base_agent import BaseAgent
from typing import Dict

class SynthesizerAgent(BaseAgent):
    """Agent that synthesizes information from multiple specialized agents."""
    
    async def synthesize_responses(self, query: str, agent_responses: Dict[str, str]) -> str:
        """Synthesize a final response from all agent outputs."""
        # Format the agent responses for the prompt
        formatted_responses = "\n\n".join([
            f"{agent_name}:\n{response}" 
            for agent_name, response in agent_responses.items()
        ])
        
        prompt = f"""
        User Query: {query}
        
        Agent Responses:
        {formatted_responses}
        
        Please synthesize a comprehensive, well-formatted final response to the user's query
        based on the information provided by the specialized agents above.
        Your response should be direct, concise, and focused on answering the query.
        """
        
        # Process and return the synthesized response as a plain string
        return await self.process(prompt)