from typing import Dict, Any, Optional, List
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from app.utils.a2a_protocol import A2AMessage, A2AProtocolHandler
from app.utils.mcp_protocol import MCPContext, MCPHandler
import uuid

class BaseAgent:
    """Base agent class with A2A and MCP support."""
    
    def __init__(
        self,
        llm: BaseChatModel,
        system_message: str,
        name: str,
        a2a_handler: Optional[A2AProtocolHandler] = None,
        mcp_handler: Optional[MCPHandler] = None
    ):
        self.llm = llm
        self.system_message = system_message
        self.name = name
        self.message_history: List[Dict[str, Any]] = []
        self.a2a_handler = a2a_handler or A2AProtocolHandler()
        self.mcp_handler = mcp_handler or MCPHandler()
    
    def add_message_to_history(self, role: str, content: str):
        """Add a message to the agent's history."""
        self.message_history.append({"role": role, "content": content})
    
    def get_messages(self):
        """Convert message history to LangChain message format."""
        messages = [SystemMessage(content=self.system_message)]
        
        for msg in self.message_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
                
        return messages
    
    async def process(self, input_text: str) -> str:
        """Process input and return a response."""
        self.add_message_to_history("user", input_text)
        response = await self.llm.ainvoke(self.get_messages())
        response_text = response.content
        self.add_message_to_history("assistant", response_text)
        return response_text
    
    async def send_a2a_message(self, 
                            receiver: str, 
                            content: str,
                            message_type: str = "text",
                            metadata: Dict[str, Any] = None,
                            thread_id: Optional[str] = None) -> str:
        """Send a message to another agent using A2A protocol."""
        if not thread_id:
            thread_id = str(uuid.uuid4())
            
        message = A2AMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            thread_id=thread_id
        )
        
        self.a2a_handler.add_message(message)
        
        # Format the message for inclusion in prompts
        formatted_message = f"\nSent message to {receiver}:\n{message.to_prompt_format()}\n"
        self.add_message_to_history("system", formatted_message)
        
        return thread_id
    
    def add_context(self, 
                   content: str,
                   context_type: str,
                   importance: float = 1.0,
                   source: Optional[str] = None) -> str:
        """Add contextual information using MCP."""
        context_id = str(uuid.uuid4())
        
        context = MCPContext(
            context_id=context_id,
            context_type=context_type,
            content=content,
            importance=importance,
            source=source or self.name
        )
        
        self.mcp_handler.add_context(context)
        return context_id
    
    def get_relevant_contexts(self, context_type: Optional[str] = None, min_importance: float = 0.5) -> str:
        """Get formatted relevant contexts for prompting."""
        contexts = self.mcp_handler.get_contexts(context_type=context_type, min_importance=min_importance)
        return self.mcp_handler.format_contexts_for_prompt(contexts)