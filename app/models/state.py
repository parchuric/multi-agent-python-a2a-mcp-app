from typing import Dict, List, Optional, Any, TypedDict, Set
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """State object for LangGraph workflow."""
    user_query: str
    identified_topic: Optional[str]
    agent_responses: Dict[str, str]
    conversation_history: List[Dict[str, Any]]
    routing_decisions: List[str]
    current_agents: Set[str]
    needs_additional_info: bool
    final_response: Optional[str]
    errors: List[str]
    metadata: Dict[str, Any]