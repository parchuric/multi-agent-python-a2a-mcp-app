from app.agents.base_agent import BaseAgent

class EvaluatorAgent(BaseAgent):
    """Agent that evaluates responses and determines if additional information is needed."""
    
    async def evaluate_responses(self, query: str, agent_responses: dict) -> dict:
        """Evaluate if the agent responses fully address the query."""
        # Format the prompt
        response_text = "\n\n".join([f"{agent}: {response}" for agent, response in agent_responses.items()])
        
        prompt = f"""
        User Query: {query}
        
        Agent Responses:
        {response_text}
        
        Evaluate if these responses fully address the user's query. 
        Consider:
        1. Are all aspects of the query addressed?
        2. Is the information accurate and complete?
        3. Is additional information needed from other agents?
        
        First explain your reasoning, then conclude with either "SUFFICIENT" if the responses adequately address the query,
        or "INSUFFICIENT" followed by what specific information is missing.
        """
        
        evaluation = await self.process(prompt)
        
        # Parse the evaluation to determine if more info is needed
        needs_more = "INSUFFICIENT" in evaluation.upper()
        
        # Return a formatted evaluation dictionary
        return {
            "needs_more_info": needs_more,
            "missing_info": evaluation
        }