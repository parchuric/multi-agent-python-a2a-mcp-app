from typing import Dict, List, Optional, Any, Union
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
    
    async def process(self, input_text: str, thread_id: Optional[str] = None) -> str:
        """Process input and return a response."""
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        # When using Responses API through MCP, we use a different approach
        if hasattr(self.mcp_handler, 'use_responses_api') and self.mcp_handler.use_responses_api:
            # First determine which other agents' contexts are relevant
            relevant_agents = await self.determine_relevant_agents(input_text)
            
            # Query with context using Responses API
            response_text = await self.mcp_handler.query_with_context(
                thread_id=thread_id,
                query=input_text,
                relevant_agents=relevant_agents
            )
            
            # Store this agent's response as context for future use
            await self.mcp_handler.update_context(
                thread_id=thread_id,
                agent_name=self.name,
                context_data=response_text
            )
            
            # Track token usage for Responses API if token counter is available
            if hasattr(self.llm, "track_responses_api_usage"):
                self.llm.track_responses_api_usage(
                    thread_id=thread_id,
                    agent_name=self.name,
                    query_length=len(input_text),
                    response_length=len(response_text)
                )
            
            return response_text
        else:
            # Traditional processing without Responses API
            self.add_message_to_history("user", input_text)
            
            # When using LangChain's AzureChatOpenAI, you need to set the property before calling
            if hasattr(self.llm, "request_timeout"):
                # Make sure to return token usage in the response
                self.llm.return_prompt_tokens = True
                self.llm.return_completion_tokens = True
            
            # Convert message history to LangChain format
            messages = self.get_messages()
            
            # Include agent name in kwargs for the middleware to use
            response = await self.llm.ainvoke(
                messages, 
                agent_name=self.name
            )
            
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
    
    async def process_received_messages(self, thread_id: Optional[str] = None) -> List[str]:
        """Process messages received from other agents.
        
        Args:
            thread_id: Optional thread ID to filter messages
            
        Returns:
            List of responses generated from processing the messages
        """
        if not self.a2a_handler:
            return []
            
        # Get messages addressed to this agent
        messages = self.a2a_handler.get_messages_for_agent(self.name, thread_id)
        
        # Sort messages by order received (assuming they have some timestamp or sequence)
        # This is a simple approach; you might want a more sophisticated ordering
        
        responses = []
        for message in messages:
            # Format the message for processing
            prompt = f"""
            You have received a message from another agent:
            
            SENDER: {message.sender}
            MESSAGE TYPE: {message.message_type}
            CONTENT: {message.content}
            
            Process this message and provide an appropriate response.
            """
            
            response = await self.process(prompt)
            responses.append(response)
            
            # Optionally, send a response back to the sender
            await self.send_a2a_message(
                receiver=message.sender,
                content=response,
                message_type="response",
                thread_id=message.thread_id
            )
            
        return responses

    async def process_query(self, query: str) -> str:
        """Default implementation that redirects to process method."""
        return await self.process(query)
    
    async def determine_relevant_agents(self, query: str) -> List[str]:
        """Determine which other agents' contexts might be relevant to this query.
        
        Args:
            query: The user query
            
        Returns:
            List of agent names that might have relevant context
        """
        # Default implementation returns all agents except self
        # In a real implementation, you'd use NLP/embeddings to find relevant agents
        
        # Get all agent names from the A2A handler if available
        all_agents = []
        if self.a2a_handler and hasattr(self.a2a_handler, "get_available_agents"):
            all_agents = self.a2a_handler.get_available_agents()
        
        # If we can't get the list from A2A handler, use a default list
        if not all_agents:
            all_agents = [
                "Analyzer", "Router", "WeatherAgent", "SportsAgent", 
                "NewsAgent", "StocksAgent", "HealthAgent", 
                "Evaluator", "Synthesizer"
            ]
        
        # Remove self from the list
        return [agent for agent in all_agents if agent != self.name]