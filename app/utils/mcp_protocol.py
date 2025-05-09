from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

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

class MCPHandler:
    """Handler for Model Context Protocol."""
    
    def __init__(self):
        self.contexts: List[MCPContext] = []
    
    def add_context(self, context: MCPContext):
        """Add a context to the handler."""
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