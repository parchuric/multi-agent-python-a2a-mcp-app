from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class A2AMessage(BaseModel):
    """Google A2A protocol message structure."""
    sender: str
    receiver: str
    message_type: str = "text"  # text, function_call, function_response, etc.
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert A2A message to dictionary format."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "thread_id": self.thread_id
        }
    
    def to_prompt_format(self) -> str:
        """Format the message for use in prompts."""
        metadata_str = ", ".join([f"{k}: {v}" for k, v in self.metadata.items()]) if self.metadata else ""
        thread_str = f"Thread: {self.thread_id}" if self.thread_id else ""
        
        return f"""
        FROM: {self.sender}
        TO: {self.receiver}
        TYPE: {self.message_type}
        {thread_str}
        {f"METADATA: {metadata_str}" if metadata_str else ""}
        
        CONTENT:
        {self.content}
        """

class A2AProtocolHandler:
    """Handler for A2A protocol messages."""
    
    def __init__(self):
        self.message_history: List[A2AMessage] = []
    
    def add_message(self, message: A2AMessage):
        """Add a message to the history."""
        self.message_history.append(message)
    
    def get_messages(self, thread_id: Optional[str] = None) -> List[A2AMessage]:
        """Get messages, optionally filtered by thread ID."""
        if thread_id:
            return [msg for msg in self.message_history if msg.thread_id == thread_id]
        return self.message_history
    
    def get_conversation_history(self, 
                                thread_id: Optional[str] = None, 
                                sender: Optional[str] = None,
                                receiver: Optional[str] = None) -> List[A2AMessage]:
        """Get filtered conversation history."""
        messages = self.message_history
        
        if thread_id:
            messages = [msg for msg in messages if msg.thread_id == thread_id]
            
        if sender:
            messages = [msg for msg in messages if msg.sender == sender]
            
        if receiver:
            messages = [msg for msg in messages if msg.receiver == receiver]
            
        return messages

    def get_messages_for_agent(self, agent_name: str, thread_id: Optional[str] = None) -> List[A2AMessage]:
        """Get messages addressed to a specific agent, optionally filtered by thread."""
        messages = [msg for msg in self.message_history if msg.receiver == agent_name]
        if thread_id:
            messages = [msg for msg in messages if msg.thread_id == thread_id]
        return messages
    
    def get_available_agents(self) -> List[str]:
        """Get a list of all available agent names."""
        # If you've registered agents, return their names
        if hasattr(self, "agents") and self.agents:
            return list(self.agents.keys())
            
        # Otherwise return a default list
        return [
            "Analyzer", "Router", "WeatherAgent", "SportsAgent", 
            "NewsAgent", "StocksAgent", "HealthAgent", 
            "Evaluator", "Synthesizer"
        ]