from app.agents.base_agent import BaseAgent

class AnalyzerAgent(BaseAgent):
    """Agent that analyzes user queries to determine the topic category."""
    
    TOPIC_CATEGORIES = [
        "weather", "sports", "news", "stocks", "health", "general"
    ]
    
    async def analyze_query(self, query: str) -> str:
        """Analyze the query and determine the primary topic category."""
        prompt = f"""
        You are an expert at categorizing user queries. Your task is to analyze the following query and determine
        the primary topic category it falls into. Choose exactly ONE category from the following list:
        
        - weather: Questions about weather conditions, forecasts, temperature, etc.
        - sports: Questions about sports teams, games, athletes, scores, etc.
        - news: Questions about current events, recent happenings, breaking news, etc.
        - stocks: Questions about financial markets, stock prices, investing, etc.
        - health: Questions about health, wellness, medical conditions, etc.
        - general: Any question that doesn't clearly fit into the above categories
        
        USER QUERY: {query}
        
        Respond with ONLY the category name, nothing else.
        """
        
        response = await self.process(prompt)
        # Clean up and validate the response
        category = response.strip().lower()
        
        # Ensure we have a valid category
        if category not in self.TOPIC_CATEGORIES:
            category = "general"
            
        return category