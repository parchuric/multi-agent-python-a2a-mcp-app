from app.agents.base_agent import BaseAgent

class ExecutorAgent(BaseAgent):
    """Agent responsible for executing steps from a plan."""
    
    async def execute_step(self, plan_step: str, context: str = "") -> str:
        """Execute a single step from the plan."""
        prompt = f"""
        You are an execution agent. Your task is to execute the following step:
        
        STEP: {plan_step}
        
        {f"CONTEXT: {context}" if context else ""}
        
        Please execute this step thoroughly and provide a detailed result of your execution.
        """
        return await self.process(prompt)