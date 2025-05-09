from app.agents.base_agent import BaseAgent

class EvaluatorAgent(BaseAgent):
    """Agent that evaluates responses and determines if additional information is needed."""
    
    async def evaluate_responses(self, query: str, responses: dict) -> dict:
        """
        Evaluate agent responses and determine if more information is needed.
        Returns a dict with 'needs_more_info' boolean and 'missing_info' explanation.
        """
        # Format the responses for the prompt
        formatted_responses = ""
        for agent, response in responses.items():
            formatted_responses += f"\n{agent}:\n{response}\n"
        
        prompt = f"""
        You are an evaluator agent. Your job is to review the responses provided by specialized agents and determine
        if the user query has been fully addressed or if additional information is needed.
        
        USER QUERY: {query}
        
        AGENT RESPONSES:
        {formatted_responses}
        
        Evaluate whether these responses fully address the user query. Consider:
        1. Is the information complete enough to provide a useful response?
        2. Are there crucial aspects of the query that haven't been addressed at all?
        3. Would additional information significantly improve the response?
        
        IMPORTANT INSTRUCTION: Be conservative about requesting more information. Only request more if absolutely essential 
        information is missing. In most cases, prefer to consider the information sufficient rather than requesting more.
        
        Respond with a JSON object with two fields:
        1. "needs_more_info": boolean (true ONLY if critical information is missing, otherwise false)
        2. "missing_info": string explanation of what information is missing or why the response is complete
        
        Example: {{"needs_more_info": false, "missing_info": "The response provides sufficient information about the weather in Seattle."}}
        """
        
        response = await self.process(prompt)
        
        # Parse the response - improved parsing logic
        try:
            import json
            import re
            
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*"needs_more_info".*"missing_info".*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                evaluation = json.loads(json_str)
                return {
                    "needs_more_info": evaluation.get("needs_more_info", False),
                    "missing_info": evaluation.get("missing_info", "")
                }
        except:
            pass
        
        # Fallback to simple text parsing if JSON parsing fails
        needs_more_info = "needs_more_info" in response.lower() and "true" in response.lower()
        
        missing_info = "The response appears to be sufficient."
        if "missing_info" in response:
            try:
                start_idx = response.find("missing_info") + len("missing_info") + 2
                end_idx = response.find('"', start_idx)
                if end_idx > start_idx:
                    missing_info = response[start_idx:end_idx].strip()
            except:
                pass
        
        return {
            "needs_more_info": needs_more_info,
            "missing_info": missing_info
        }