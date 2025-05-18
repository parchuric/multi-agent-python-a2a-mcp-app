from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import uuid
import logging
from app.utils.responses_api import ResponsesApiHandler  # Add this import

class MCPContext(BaseModel):
    """Model Context Protocol context structure."""
    context_id: str
    context_type: str  # e.g., "memory", "knowledge", "reasoning", etc.
    content: str
    importance: float = 1.0  # 0.0 to 1.0
    timestamp: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MCP context to dictionary format."""
        return {
            "context_id": self.context_id,
            "context_type": self.context_type,
            "content": self.content,
            "importance": self.importance,
            "timestamp": self.timestamp,
            "source": self.source,
            "metadata": self.metadata
        }

# Configure logging
logger = logging.getLogger(__name__)

class MCPHandler:
    """Handler for Model Context Protocol with Responses API support."""
    
    def __init__(self, use_responses_api=False):  # Updated constructor
        self.contexts: List[MCPContext] = []
        self.thread_contexts: Dict[str, Dict[str, Any]] = {}  # thread_id -> agent_name -> context
        self.use_responses_api = use_responses_api
        
        if use_responses_api:
            self.responses_handler = ResponsesApiHandler()
            # Try to load saved conversations
            self.responses_handler.load_conversations()
            logger.info("Initialized MCPHandler with Responses API support")
    
    def add_context(self, context: MCPContext):
        """Add a context to the handler (legacy method)."""
        self.contexts.append(context)
    
    def get_contexts(self, 
                    context_type: Optional[str] = None, 
                    min_importance: float = 0.0,
                    source: Optional[str] = None) -> List[MCPContext]:
        """Get contexts with optional filtering."""
        filtered = self.contexts
        
        if context_type:
            filtered = [ctx for ctx in filtered if ctx.context_type == context_type]
            
        filtered = [ctx for ctx in filtered if ctx.importance >= min_importance]
        
        if source:
            filtered = [ctx for ctx in filtered if ctx.source == source]
            
        # Sort by importance (descending)
        return sorted(filtered, key=lambda x: x.importance, reverse=True)
    
    def get_context_by_id(self, context_id: str) -> Optional[MCPContext]:
        """Get a specific context by ID."""
        for ctx in self.contexts:
            if ctx.context_id == context_id:
                return ctx
        return None
    
    def format_contexts_for_prompt(self, contexts: List[MCPContext]) -> str:
        """Format contexts for inclusion in prompts."""
        result = "CONTEXTUAL INFORMATION:\n\n"
        
        for i, ctx in enumerate(contexts):
            result += f"[{i+1}] {ctx.context_type.upper()} (Importance: {ctx.importance})\n"
            if ctx.source:
                result += f"Source: {ctx.source}\n"
            result += f"{ctx.content}\n\n"
            
        return result
    
    async def update_context(self, thread_id: str, agent_name: str, context_data: str) -> None:
        """Store context for an agent in a thread."""
        if self.use_responses_api:
            await self.responses_handler.store_context(thread_id, agent_name, context_data)
            logger.debug(f"Stored context via Responses API for agent {agent_name} in thread {thread_id}")
        else:
            # Traditional context storage
            if thread_id not in self.thread_contexts:
                self.thread_contexts[thread_id] = {}
            self.thread_contexts[thread_id][agent_name] = context_data
            logger.debug(f"Stored context locally for agent {agent_name} in thread {thread_id}")
    
    async def get_agent_context(self, thread_id: str, agent_name: Optional[str] = None) -> Any:
        """Get context for a thread and specific agent."""
        if self.use_responses_api:
            # For responses API, we return nothing here since contexts are referenced during queries
            logger.debug(f"Using Responses API - context references handled during query")
            return None
        else:
            # Traditional context retrieval
            if thread_id not in self.thread_contexts:
                return None
                
            if agent_name:
                return self.thread_contexts[thread_id].get(agent_name)
            else:
                return self.thread_contexts[thread_id]
    
    async def query_with_context(self, thread_id: str, query: str, relevant_agents: Optional[List[str]] = None) -> str:
        """Query with context using Responses API."""
        if not self.use_responses_api:
            raise NotImplementedError("This method requires Responses API to be enabled")
            
        return await self.responses_handler.query_with_context(thread_id, query, relevant_agents)
    
    def persist(self, filepath: str = "data/conversations.json") -> None:
        """Persist context/conversation data."""
        if self.use_responses_api:
            self.responses_handler.persist_conversations(filepath)
            logger.info(f"Persisted conversation data to {filepath}")