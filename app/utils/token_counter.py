from typing import Any, Dict, List
import time
import json
import os
from datetime import datetime

class TokenCounterMiddleware:
    """Middleware to count tokens for Azure OpenAI calls."""
    
    def __init__(self, llm, log_file=None):
        self.llm = llm
        self.call_history = []
        self.log_file = log_file or f"token_usage_{datetime.now().strftime('%Y%m%d')}.json"
    
    async def ainvoke(self, messages, **kwargs):
        """Wrap the LLM's ainvoke method to count tokens."""
        start_time = time.time()
        
        # Extract agent_name from kwargs but don't pass it to the underlying LLM
        agent_name = kwargs.pop("agent_name", self.get_agent_name())
        
        # Make the actual API call without agent_name parameter
        response = await self.llm.ainvoke(messages, **kwargs)
        
        # Debug logging
        print(f"Response type: {type(response)}")
        print(f"Response attrs: {dir(response)}")
        
        # Extract token usage from Azure OpenAI response - modify based on actual response structure
        token_usage = {}
        
        # Try multiple ways to extract token usage
        if hasattr(response, "usage"):
            # Direct usage attribute
            usage = response.usage
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0)
            }
        elif hasattr(response, "_response") and "usage" in response._response:
            # Nested in _response
            usage = response._response["usage"]
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        elif hasattr(response, "llm_output") and response.llm_output and "token_usage" in response.llm_output:
            # LangChain format
            usage = response.llm_output["token_usage"]
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        else:
            # Fallback: estimate tokens using tiktoken
            try:
                import tiktoken
                encoding = tiktoken.encoding_for_model("gpt-4")
                
                # Calculate prompt tokens
                prompt_tokens = 0
                for message in messages:
                    if hasattr(message, "content"):
                        prompt_tokens += len(encoding.encode(message.content))
                    elif isinstance(message, dict) and "content" in message:
                        prompt_tokens += len(encoding.encode(message["content"]))
                
                # Calculate completion tokens
                completion_text = ""
                if hasattr(response, "content"):
                    completion_text = response.content
                elif hasattr(response, "message") and hasattr(response.message, "content"):
                    completion_text = response.message.content
                
                completion_tokens = len(encoding.encode(completion_text))
                
                token_usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }
                print(f"Estimated tokens: {token_usage}")
            except Exception as e:
                print(f"Token estimation failed: {e}")
                
        # Create usage record with the extracted agent_name
        usage_record = {
            "timestamp": time.time(),
            "duration": time.time() - start_time,
            "model": getattr(self.llm, "model", "unknown"),
            "tokens": token_usage,
            "agent": agent_name,  # Use the extracted agent_name
            "success": True
        }
        
        # Debug logging
        print(f"Recording usage: {usage_record}")
        
        # Save to history
        self.call_history.append(usage_record)
        
        # Log to file
        self._append_to_log(usage_record)
        
        return response
    
    def _append_to_log(self, record):
        """Append usage record to log file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.log_file) or '.', exist_ok=True)
            
            # Write to file
            with open(self.log_file, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"Failed to write token usage log: {e}")
    
    def get_total_usage(self):
        """Get total token usage across all calls."""
        prompt_tokens = sum(
            call["tokens"].get("prompt_tokens", 0) for call in self.call_history
        )
        completion_tokens = sum(
            call["tokens"].get("completion_tokens", 0) for call in self.call_history
        )
        total_tokens = sum(
            call["tokens"].get("total_tokens", 0) for call in self.call_history
        )
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "call_count": len(self.call_history)
        }
    
    def get_usage_by_agent(self):
        """Get token usage grouped by agent."""
        agent_usage = {}
        
        for call in self.call_history:
            agent = call.get("agent", "unknown")
            if agent not in agent_usage:
                agent_usage[agent] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "call_count": 0
                }
            
            tokens = call.get("tokens", {})
            agent_usage[agent]["prompt_tokens"] += tokens.get("prompt_tokens", 0)
            agent_usage[agent]["completion_tokens"] += tokens.get("completion_tokens", 0)
            agent_usage[agent]["total_tokens"] += tokens.get("total_tokens", 0)
            agent_usage[agent]["call_count"] += 1
            
        return agent_usage

    def get_agent_name(self):
        """Try to determine the agent name from the call stack."""
        import inspect
        frames = inspect.stack()
        for frame in frames:
            if "agent" in frame.filename.lower() and "base_agent" not in frame.filename.lower():
                filename = os.path.basename(frame.filename)
                agent_name = filename.replace("_agent.py", "").replace(".py", "")
                return agent_name.capitalize() + "Agent"
        return "unknown"

def generate_token_usage_report(token_counter):
    """Generate a comprehensive token usage report."""
    if not hasattr(token_counter, "get_total_usage"):
        return "Token counter not available or doesn't have usage data."
        
    total_usage = token_counter.get_total_usage()
    agent_usage = token_counter.get_usage_by_agent()
    
    # Calculate costs (approximate)
    input_cost_per_1k = 0.003  # Azure GPT-4 input cost per 1K tokens
    output_cost_per_1k = 0.006  # Azure GPT-4 output cost per 1K tokens
    
    prompt_cost = total_usage["prompt_tokens"] * input_cost_per_1k / 1000
    completion_cost = total_usage["completion_tokens"] * output_cost_per_1k / 1000
    total_cost = prompt_cost + completion_cost
    
    # Format the report
    report = [
        "==== Token Usage Report ====",
        f"Total API Calls: {total_usage['call_count']}",
        f"Total Prompt Tokens: {total_usage['prompt_tokens']}",
        f"Total Completion Tokens: {total_usage['completion_tokens']}",
        f"Total Tokens: {total_usage['total_tokens']}",
        f"Estimated Cost: ${total_cost:.4f} (${prompt_cost:.4f} input + ${completion_cost:.4f} output)",
        "\n==== Usage by Agent ===="
    ]
    
    for agent, usage in agent_usage.items():
        agent_prompt_cost = usage["prompt_tokens"] * input_cost_per_1k / 1000
        agent_completion_cost = usage["completion_tokens"] * output_cost_per_1k / 1000
        agent_total_cost = agent_prompt_cost + agent_completion_cost
        
        report.append(f"\nAgent: {agent}")
        report.append(f"  API Calls: {usage['call_count']}")
        report.append(f"  Prompt Tokens: {usage['prompt_tokens']}")
        report.append(f"  Completion Tokens: {usage['completion_tokens']}")
        report.append(f"  Total Tokens: {usage['total_tokens']}")
        report.append(f"  Estimated Cost: ${agent_total_cost:.4f}")
    
    return "\n".join(report)