from app.agents.base_agent import BaseAgent
from typing import Dict

class SynthesizerAgent(BaseAgent):
    """Agent that synthesizes information from multiple specialized agents."""
    
    async def synthesize_responses(self, query: str, responses: Dict[str, str]) -> str:
        """Combine information from multiple responses into a cohesive answer."""
        # Format the responses for the prompt
        formatted_responses = ""
        for agent, response in responses.items():
            formatted_responses += f"\n{agent}:\n{response}\n"
        
        prompt = f"""
        You are a synthesis expert. Your task is to combine information from multiple specialized agents into
        a cohesive, comprehensive response that best addresses the user's query.
        
        USER QUERY: {query}
        
        AGENT RESPONSES:
        {formatted_responses}
        
        Create a unified response that:
        1. Integrates information from all relevant responses
        2. Eliminates redundancies
        3. Resolves any contradictions by providing balanced perspective
        4. Presents a clear, conversational answer that directly addresses the user's query
        5. Attributes information to appropriate sources when relevant
        
        Your response should be comprehensive but concise, and should feel like a single, coherent answer rather
        than a compilation of separate responses.
        """
        
        return await self.process(prompt)