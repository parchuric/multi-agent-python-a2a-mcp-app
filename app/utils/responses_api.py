from openai import AzureOpenAI
from typing import Dict, List, Optional, Any
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class ResponsesApiHandler:
    """Handler for Azure OpenAI Responses API integration."""
    
    def __init__(self, client=None):
        """Initialize the Responses API handler."""
        if client:
            self.client = client
        else:
            # Force the correct API version here
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")
            self.client = AzureOpenAI(
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=api_version,  # Use the environment variable or default to latest preview
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
            )
        self.conversation_ids = {}  # thread_id -> conversation_id mapping
        self.response_references = {}  # thread_id -> {agent -> response_id}
        
    async def get_conversation_id(self, thread_id: str) -> str:
        """Get or create a conversation ID for a thread."""
        if thread_id not in self.conversation_ids:
            # Initialize a new conversation
            self.conversation_ids[thread_id] = str(uuid.uuid4())
            self.response_references[thread_id] = {}
            logger.info(f"Created new conversation ID {self.conversation_ids[thread_id]} for thread {thread_id}")
        return self.conversation_ids[thread_id]
        
    # Update the store_context method to ensure synchronous operation in fallback mode
    async def store_context(self, thread_id: str, agent_name: str, context_data: str) -> str:
        """Store context using Responses API."""
        try:
            conversation_id = await self.get_conversation_id(thread_id)
            
            # Create a message that will be stored server-side
            response = await self.client.chat.completions.create(
                model=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
                messages=[
                    {"role": "system", "content": f"Context from {agent_name}"},
                    {"role": "user", "content": context_data}
                ],
                conversation_id=conversation_id,
                response_id=True
            )
            
            # Store the response ID for future reference
            self.response_references[thread_id][agent_name] = response.id
            logger.info(f"Stored context for {agent_name} in thread {thread_id}, response ID: {response.id}")
            
            return response.id
        except TypeError as e:
            # Handle case where Responses API isn't supported
            if "unexpected keyword argument 'conversation_id'" in str(e):
                logger.warning("Responses API not supported by current API version. Falling back to standard API.")
                # IMPORTANT: Don't use await here
                response = self.client.chat.completions.create(
                    model=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
                    messages=[
                        {"role": "system", "content": f"Context from {agent_name}"},
                        {"role": "user", "content": context_data}
                    ]
                )
                # Store content instead of response ID
                if thread_id not in self.response_references:
                    self.response_references[thread_id] = {}
                self.response_references[thread_id][agent_name] = response.choices[0].message.content
                return "fallback-mode"
            else:
                logger.error(f"TypeError in store_context: {e}")
                raise
        except Exception as e:
            logger.error(f"Error in store_context: {e}")
            raise
    
    async def query_with_context(self, 
                               thread_id: str, 
                               query: str, 
                               relevant_agents: Optional[List[str]] = None) -> str:
        """Query with context references."""
        try:
            conversation_id = await self.get_conversation_id(thread_id)
            
            # Build references to relevant agent contexts
            references = []
            if relevant_agents and thread_id in self.response_references:
                for agent in relevant_agents:
                    if agent in self.response_references[thread_id]:
                        references.append({"response_id": self.response_references[thread_id][agent]})
            
            # Make API call with response references - REMOVE AWAIT HERE
            logger.info(f"Querying with {len(references)} context references for thread {thread_id}")
            response = self.client.chat.completions.create(  # No await
                model=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
                messages=[{"role": "user", "content": query}],
                conversation_id=conversation_id,
                references=references
            )
            
            return response.choices[0].message.content
        except TypeError as e:
            # Handle case where Responses API isn't supported
            if "unexpected keyword argument 'conversation_id'" in str(e):
                logger.warning("Responses API not supported by current API version. Using fallback mode.")
                
                # In fallback mode, we'll construct a prompt with the stored context
                context_prompt = ""
                if relevant_agents and thread_id in self.response_references:
                    for agent in relevant_agents:
                        if agent in self.response_references[thread_id]:
                            agent_context = self.response_references[thread_id][agent]
                            if len(agent_context) > 500:  # Truncate if too long
                                agent_context = agent_context[:500] + "..."
                            context_prompt += f"\n\nContext from {agent}:\n{agent_context}"
                
                # Create a combined prompt with the query and context
                messages = [
                    {"role": "system", "content": "You have access to previous context. Consider it when answering the query."},
                    {"role": "user", "content": f"{context_prompt}\n\nCurrent query: {query}"}
                ]
                
                response = self.client.chat.completions.create(
                    model=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
                    messages=messages
                )
                
                return response.choices[0].message.content
            else:
                raise
    
    async def test_responses_api_support(self) -> bool:
        """Test if the current Azure OpenAI setup supports Responses API."""
        try:
            # Generate a test conversation ID
            conversation_id = str(uuid.uuid4())
            
            # Try to use a Responses API feature
            try:
                response = self.client.chat.completions.create(
                    model=os.environ["AZURE_OPENAI_DEPLOYMENT_ID"],
                    messages=[{"role": "user", "content": "This is a test message"}],
                    conversation_id=conversation_id,
                    response_id=True
                )
                logger.info("Responses API is supported by your Azure OpenAI deployment")
                return True
            except TypeError as e:
                if "unexpected keyword argument" in str(e):
                    logger.warning("Responses API is not supported by your Azure OpenAI deployment")
                    return False
                raise
        except Exception as e:
            logger.error(f"Error testing Responses API: {e}")
            return False
    
    def persist_conversations(self, filepath: str = "conversations.json") -> None:
        """Persist conversation mappings to disk."""
        import json
        
        data = {
            "conversation_ids": self.conversation_ids,
            "response_references": self.response_references
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f)
        logger.info(f"Persisted {len(self.conversation_ids)} conversations to {filepath}")
    
    def load_conversations(self, filepath: str = "conversations.json") -> bool:
        """Load conversation mappings from disk."""
        import json
        import os
        
        if not os.path.exists(filepath):
            logger.warning(f"Conversation file {filepath} not found")
            return False
            
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                
            self.conversation_ids = data.get("conversation_ids", {})
            self.response_references = data.get("response_references", {})
            logger.info(f"Loaded {len(self.conversation_ids)} conversations from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            return False