import re
import uuid
from typing import Dict, List, Any
from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.critic_agent import CriticAgent
from app.utils.a2a_protocol import A2AProtocolHandler
from app.utils.mcp_protocol import MCPHandler

class MultiAgentChain:
    """Orchestrates the multi-agent workflow with A2A and MCP support."""
    
    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        critic: CriticAgent,
        a2a_handler: A2AProtocolHandler = None,
        mcp_handler: MCPHandler = None
    ):
        # Initialize A2A and MCP handlers if not provided
        self.a2a_handler = a2a_handler or A2AProtocolHandler()
        self.mcp_handler = mcp_handler or MCPHandler()
        
        # Share the same handlers across all agents
        self.planner = planner
        self.planner.a2a_handler = self.a2a_handler
        self.planner.mcp_handler = self.mcp_handler
        
        self.executor = executor
        self.executor.a2a_handler = self.a2a_handler
        self.executor.mcp_handler = self.mcp_handler
        
        self.critic = critic
        self.critic.a2a_handler = self.a2a_handler
        self.critic.mcp_handler = self.mcp_handler
        
        self.execution_context = ""
        self.main_thread_id = None
    
    def parse_plan(self, plan_text: str) -> List[str]:
        """Parse a plan into individual steps."""
        # Simple regex to find numbered steps in the plan
        steps = re.findall(r'^\s*\d+\.\s*(.*?)(?=^\s*\d+\.|\Z)', plan_text, re.MULTILINE | re.DOTALL)
        if not steps:
            # Fallback if regex doesn't find steps
            steps = [line.strip() for line in plan_text.split('\n') if line.strip()]
        return [step.strip() for step in steps]
    
    async def execute(self, user_task: str) -> Dict[str, Any]:
        """Execute the full multi-agent workflow using A2A and MCP."""
        # Initialize main thread ID for the conversation
        self.main_thread_id = str(uuid.uuid4())
        
        # Add the task as a high-importance context
        self.planner.add_context(
            content=user_task,
            context_type="task",
            importance=1.0,
            source="user"
        )
        
        # 1. Generate plan
        plan_prompt = f"""
        {self.planner.get_relevant_contexts()}
        
        Your task is to create a detailed plan to solve this problem:
        {user_task}
        
        Provide a clear step-by-step plan with numbered steps.
        """
        
        plan_text = await self.planner.process(plan_prompt)
        plan_steps = self.parse_plan(plan_text)
        
        # Add plan to context
        plan_context_id = self.planner.add_context(
            content=plan_text,
            context_type="plan",
            importance=0.9
        )
        
        # Send plan to executor using A2A
        plan_thread_id = await self.planner.send_a2a_message(
            receiver="Executor",
            content=f"Here's the plan to execute: \n\n{plan_text}",
            message_type="plan",
            thread_id=self.main_thread_id
        )
        
        results = {
            "task": user_task,
            "plan": plan_text,
            "steps": []
        }
        
        # 2. Execute each step and evaluate
        for i, step in enumerate(plan_steps):
            # Add step context
            step_context_id = self.executor.add_context(
                content=step,
                context_type="plan_step",
                importance=0.8,
                source="Planner"
            )
            
            # Get relevant contexts for this step
            relevant_contexts = self.executor.get_relevant_contexts()
            
            # Execute step
            execution_result = await self.executor.execute_step(
                step, 
                f"{relevant_contexts}\n{self.execution_context}"
            )
            
            # Add execution result to context
            exec_context_id = self.executor.add_context(
                content=execution_result,
                context_type="execution_result",
                importance=0.8
            )
            
            # Send execution result to critic using A2A
            await self.executor.send_a2a_message(
                receiver="Critic",
                content=f"I've executed step {i+1}: '{step}' with result: \n\n{execution_result}",
                message_type="execution_result",
                thread_id=self.main_thread_id
            )
            
            # Evaluate execution
            evaluation = await self.critic.evaluate(step, execution_result)
            
            # Add evaluation to context
            eval_context_id = self.critic.add_context(
                content=evaluation,
                context_type="evaluation",
                importance=0.7
            )
            
            # Send evaluation back to executor using A2A
            await self.critic.send_a2a_message(
                receiver="Executor",
                content=f"My evaluation of your execution of step {i+1}: \n\n{evaluation}",
                message_type="evaluation",
                thread_id=self.main_thread_id
            )
            
            # Add to execution context for next steps
            self.execution_context += f"\nStep {i+1} Result: {execution_result}\nEvaluation: {evaluation}\n"
            
            # Record results
            results["steps"].append({
                "step_number": i + 1,
                "step_description": step,
                "execution_result": execution_result,
                "evaluation": evaluation
            })
        
        # Final message from planner
        await self.planner.send_a2a_message(
            receiver="user",
            content=f"We have completed all {len(plan_steps)} steps of the plan. The task has been executed.",
            message_type="completion",
            thread_id=self.main_thread_id
        )
        
        results["final_context"] = self.execution_context
        results["a2a_message_count"] = len(self.a2a_handler.message_history)
        results["mcp_context_count"] = len(self.mcp_handler.contexts)
        
        return results