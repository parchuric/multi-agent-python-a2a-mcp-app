from app.agents.base_agent import BaseAgent

class CriticAgent(BaseAgent):
    """Agent responsible for evaluating execution results and providing feedback."""
    
    async def evaluate(self, plan_step: str, execution_result: str) -> str:
        """Evaluate the execution result against the plan step."""
        prompt = f"""
        You are a critic agent. Evaluate the following execution result against the planned step:
        
        PLANNED STEP: {plan_step}
        
        EXECUTION RESULT: {execution_result}
        
        Provide constructive feedback:
        1. Is the execution complete and correct?
        2. Are there any issues or improvements needed?
        3. Suggest improvements if necessary.
        """
        return await self.process(prompt)