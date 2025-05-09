from app.agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for creating plans to solve tasks."""
    
    async def create_plan(self, user_task: str) -> str:
        """Create a detailed plan based on the user task."""
        prompt = f"""
        You are a planning agent. Your task is to create a detailed step-by-step plan to solve the following problem:
        
        USER TASK: {user_task}
        
        Provide a clear, detailed plan with numbered steps. Each step should be specific enough for execution.
        """
        return await self.process(prompt)