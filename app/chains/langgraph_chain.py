from typing import Dict, List, Any, Annotated, TypedDict, Set, Tuple, Optional
from langgraph.graph import StateGraph, END
from app.models.state import AgentState
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.router_agent import RouterAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.synthesizer_agent import SynthesizerAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.sports_agent import SportsAgent
from app.agents.news_agent import NewsAgent
from app.agents.stocks_agent import StocksAgent
from app.agents.health_agent import HealthAgent
from app.utils.a2a_protocol import A2AProtocolHandler
from app.utils.mcp_protocol import MCPHandler
import uuid
import logging

logger = logging.getLogger(__name__)

class MultiAgentLangGraph:
    """LangGraph implementation of multi-agent workflow with specialized agents."""
    
    def __init__(
        self,
        analyzer: AnalyzerAgent,
        router: RouterAgent,
        weather_agent: WeatherAgent,
        sports_agent: SportsAgent,
        news_agent: NewsAgent,
        stocks_agent: StocksAgent,
        health_agent: HealthAgent,
        evaluator: EvaluatorAgent,
        synthesizer: SynthesizerAgent,
        a2a_handler: A2AProtocolHandler = None,
        mcp_handler: MCPHandler = None,
        recursion_limit: int = 3  # Parameter is defined here
    ):
        # Add this line to save recursion_limit as an instance attribute
        self.recursion_limit = recursion_limit
        
        self.analyzer = analyzer
        self.router = router
        self.weather_agent = weather_agent
        self.sports_agent = sports_agent
        self.news_agent = news_agent
        self.stocks_agent = stocks_agent
        self.health_agent = health_agent
        self.evaluator = evaluator
        self.synthesizer = synthesizer
        
        # Initialize A2A and MCP handlers if not provided
        self.a2a_handler = a2a_handler or A2AProtocolHandler()
        self.mcp_handler = mcp_handler or MCPHandler()
        
        # Share the handlers across all agents
        for agent in [analyzer, router, weather_agent, sports_agent, news_agent, 
                     stocks_agent, health_agent, evaluator, synthesizer]:
            agent.a2a_handler = self.a2a_handler
            agent.mcp_handler = self.mcp_handler
        
        # Create the agent mapping for dynamic access
        self.agent_mapping = {
            "WeatherAgent": weather_agent,
            "SportsAgent": sports_agent,
            "NewsAgent": news_agent,
            "StocksAgent": stocks_agent,
            "HealthAgent": health_agent
        }
        
        # Build the graph
        self.workflow = self._build_graph()
        self.recursion_limit = recursion_limit
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Initialize the graph with our state type
        graph = StateGraph(AgentState)
        
        # Add all nodes
        graph.add_node("analyzer", self._analyze_query)
        graph.add_node("router", self._route_query)
        graph.add_node("process_agents", self._process_with_agents)
        graph.add_node("evaluator", self._evaluate_responses)
        graph.add_node("synthesizer", self._synthesize_responses)
        
        # Define the edges
        graph.add_edge("analyzer", "router")
        graph.add_edge("router", "process_agents")
        graph.add_edge("process_agents", "evaluator")
        
        # Conditional edge from evaluator
        graph.add_conditional_edges(
            "evaluator",
            self._needs_more_info,
            {
                "needs_more_info": "router",
                "complete": "synthesizer"
            }
        )
        
        # End after synthesizer
        graph.add_edge("synthesizer", END)
        
        # Set entry point
        graph.set_entry_point("analyzer")
        
        # Compile without the recursion_limit parameter
        # Different versions of LangGraph have different parameters for compile()
        try:
            # Try with config dict approach (newer versions)
            return graph.compile(config={"recursion_limit": self.recursion_limit})
        except TypeError:
            try:
                # Try with direct parameter (some versions)
                return graph.compile(recursion_limit=self.recursion_limit)
            except TypeError:
                # Fallback to no parameters if neither is supported
                return graph.compile()
    
    async def _analyze_query(self, state: AgentState) -> AgentState:
        """Node function for analyzing the user query."""
        logger.info(f"Analyzing query: {state['user_query']}")
        
        # Get the topic category
        topic = await self.analyzer.analyze_query(state["user_query"])
        
        # Record the identified topic in state
        state["identified_topic"] = topic
        
        # Record in conversation history
        state["conversation_history"].append({
            "agent": "Analyzer",
            "action": "topic_identification",
            "result": topic
        })
        
        # Add to context using MCP
        self.analyzer.add_context(
            content=f"The query topic has been identified as: {topic}",
            context_type="topic_identification",
            importance=0.9
        )
        
        # Use A2A protocol to communicate the result to the router
        await self.analyzer.send_a2a_message(
            receiver="Router",
            content=f"I've identified the query topic as: {topic}",
            message_type="topic_identification",
            thread_id=str(state.get("metadata", {}).get("thread_id", uuid.uuid4()))
        )
        
        return state
    
    async def _route_query(self, state: AgentState) -> AgentState:
        """Node function for routing the query to appropriate agents."""
        logger.info(f"Routing query with topic: {state['identified_topic']}")
        
        # Get routing decisions
        agent_names = await self.router.route_query(state["user_query"], state["identified_topic"])
        
        # Record the routing decisions in state
        state["routing_decisions"] = agent_names
        state["current_agents"] = set(agent_names)
        
        # Record in conversation history
        state["conversation_history"].append({
            "agent": "Router",
            "action": "routing_decision",
            "result": agent_names
        })
        
        # Add to context using MCP
        self.router.add_context(
            content=f"The query has been routed to: {', '.join(agent_names)}",
            context_type="routing_decision",
            importance=0.8
        )
        
        # Use A2A protocol to communicate with each selected agent
        for agent_name in agent_names:
            await self.router.send_a2a_message(
                receiver=agent_name,
                content=f"Please process this query: {state['user_query']}",
                message_type="query_routing",
                thread_id=str(state.get("metadata", {}).get("thread_id", uuid.uuid4()))
            )
        
        return state
    
    async def _process_with_agents(self, state: AgentState) -> AgentState:
        """Node function for processing the query with selected specialized agents."""
        logger.info(f"Processing with agents: {state['routing_decisions']}")
        
        # Initialize agent responses if not already present
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        
        # Process with each selected agent
        for agent_name in state["current_agents"]:
            if agent_name in self.agent_mapping:
                agent = self.agent_mapping[agent_name]
                
                # Process query with the specialized agent
                response = await agent.process_query(state["user_query"])
                
                # Store the response
                state["agent_responses"][agent_name] = response
                
                # Record in conversation history
                state["conversation_history"].append({
                    "agent": agent_name,
                    "action": "query_processing",
                    "result": response
                })
                
                # Add to context using MCP
                agent.add_context(
                    content=response,
                    context_type="agent_response",
                    importance=0.9,
                    source=agent_name
                )
        
        return state
    
    async def _evaluate_responses(self, state: AgentState) -> AgentState:
        """Node function for evaluating if the responses fully address the query."""
        logger.info("Evaluating responses for completeness")
        
        # Initialize routing attempts counter if not exists
        if "routing_attempts" not in state["metadata"]:
            state["metadata"]["routing_attempts"] = 1
        else:
            state["metadata"]["routing_attempts"] += 1
        
        # If we've tried routing too many times, force completion
        if state["metadata"]["routing_attempts"] >= self.recursion_limit:
            logger.info(f"Reached routing attempt limit ({self.recursion_limit}). Forcing completion.")
            state["needs_additional_info"] = False
            
            # Add note about this to the conversation history
            state["conversation_history"].append({
                "agent": "Evaluator",
                "action": "forced_completion",
                "result": "Maximum routing attempts reached."
            })
            return state
        
        # Evaluate the responses - MODIFY THIS SECTION
        try:
            # Check if the responses are dictionary objects as expected
            if not isinstance(state["agent_responses"], dict):
                logger.warning(f"Expected agent_responses to be dict, got {type(state['agent_responses'])}")
                evaluation = {
                    "needs_more_info": False,
                    "missing_info": "Could not process agent responses properly."
                }
            else:
                evaluation = await self.evaluator.evaluate_responses(state["user_query"], state["agent_responses"])
                
                # If evaluation is returned as a string instead of a dict, convert it
                if isinstance(evaluation, str):
                    # Parse the string response to determine if more info is needed
                    needs_more = "INSUFFICIENT" in evaluation.upper() or "INCOMPLETE" in evaluation.upper()
                    evaluation = {
                        "needs_more_info": needs_more,
                        "missing_info": evaluation
                    }
        
        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            # Provide a fallback evaluation
            evaluation = {
                "needs_more_info": False,
                "missing_info": f"Error during evaluation: {str(e)}"
            }
        
        # Add evaluation result to state
        state["needs_additional_info"] = evaluation["needs_more_info"]
        
        # If we need more info, update current agents to exclude already consulted ones
        if state["needs_additional_info"]:
            # Get agent names that weren't in the current round
            all_agents = set(self.agent_mapping.keys())
            used_agents = set(state["routing_decisions"])
            new_agents = all_agents - used_agents
            
            if new_agents:
                state["current_agents"] = new_agents
            else:
                # If we've used all agents, no need for more info
                state["needs_additional_info"] = False
        
        # Record in conversation history
        state["conversation_history"].append({
            "agent": "Evaluator",
            "action": "response_evaluation",
            "result": evaluation
        })
        
        # Add to context using MCP
        self.evaluator.add_context(
            content=f"Response evaluation: {evaluation['missing_info']}",
            context_type="evaluation",
            importance=0.8
        )
        
        return state
    
    async def _synthesize_responses(self, state: AgentState) -> AgentState:
        """Node function for synthesizing responses from multiple agents."""
        logger.info("Synthesizing final response")
        
        try:
            # Add debug information
            logger.debug(f"Agent responses: {state.get('agent_responses', {})}")
            
            # Synthesize the final response
            final_response = await self.synthesizer.synthesize_responses(state["user_query"], state["agent_responses"])
            
            # Add extensive debug information
            logger.debug(f"Final response type: {type(final_response)}")
            if isinstance(final_response, str):
                logger.debug(f"Final response (str): {final_response[:100]}...")
            else:
                logger.debug(f"Final response (not str): {final_response}")
            
            # Always convert to string if not already
            if not isinstance(final_response, str):
                final_response = str(final_response)
            
            # Directly use the string response
            state["final_response"] = final_response
            
            # Record in conversation history
            state["conversation_history"].append({
                "agent": "Synthesizer",
                "action": "final_synthesis",
                "result": final_response
            })
            
            # Add to context using MCP
            self.synthesizer.add_context(
                content=final_response,
                context_type="final_response",
                importance=1.0
            )
            
        except Exception as e:
            logger.error(f"Error during synthesis: {str(e)}")
            logger.exception("Detailed traceback")
            # Provide a fallback response
            state["final_response"] = "I apologize, but I encountered an issue while generating a response."
            
        return state
    
    def _needs_more_info(self, state: AgentState) -> str:
        """Conditional edge function that determines if we need more information."""
        if state["needs_additional_info"] and state["current_agents"]:
            logger.info("Routing for additional information")
            return "needs_more_info"
        else:
            logger.info("Information is complete, proceeding to synthesis")
            return "complete"
    
    async def process_query(self, query: str) -> Dict:
        """Process a query through the multi-agent workflow."""
        # Initialize thread ID for this conversation
        thread_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state = {
            "user_query": query,
            "conversation_history": [],  # Initialize empty conversation history
            "metadata": {
                "thread_id": thread_id
            }
        }
        
        try:
            # Run the graph (changed from self.graph to self.workflow)
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Return a comprehensive result dictionary
            return {
                "response": final_state.get("final_response", "No response generated"),
                "topic": final_state.get("topic", "unknown"),
                "agents_consulted": list(final_state.get("agent_responses", {}).keys()),
                "conversation_history": final_state.get("conversation_history", [])
            }
        
        except Exception as e:
            logger.error(f"Error during query processing: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "response": f"Error processing query: {str(e)}",
                "topic": "error",
                "agents_consulted": [],
                "conversation_history": []
            }

# First process any received messages from other agents. Then perform the agent's primary function
async def _send_messages_to_next_agents(self, state: AgentState) -> None:
    """
    Send messages to the next agents in the workflow as needed.
    This method iterates through the list of current agents in the state and sends 
    an agent-to-agent (A2A) message to each of them. The message contains the user query 
    and is routed using the "query_routing" message type. A thread ID is included in the 
    message metadata to track the communication thread.
    Args:
        state (AgentState): The current state of the workflow, which includes:
            - current_agents (list): A list of agent names to send messages to.
            - user_query (str): The query provided by the user.
            - metadata (dict, optional): Additional metadata, including a thread ID.
    Raises:
        KeyError: If an agent in `current_agents` is not found in `self.agent_mapping`.
    Notes:
        - The `agent_mapping` attribute is used to resolve agent names to agent objects.
        - A new UUID is generated for the thread ID if it is not provided in the metadata.
    """
    """Send messages to the next agents in the workflow as needed."""
    for agent_name in state["current_agents"]:
        if agent_name in self.agent_mapping:
            agent = self.agent_mapping[agent_name]
            await agent.send_a2a_message(
                receiver=agent_name,
                content=f"Please process this query: {state['user_query']}",
                message_type="query_routing",
                thread_id=str(state.get("metadata", {}).get("thread_id", uuid.uuid4()))
            )
    async def _run_analyzer_node(self, state):
        """Run the analyzer agent to identify the topic and entities in the query."""
        # First process any received messages
        await self.analyzer.process_received_messages(
            thread_id=str(state.get("metadata", {}).get("thread_id", ""))
        )
        
        # Then perform the analyzer's primary function
        topic = await self.analyzer.process(f"Analyze this query: {state['user_query']}")
        
        # Use A2A protocol to communicate the result to the router
        await self.analyzer.send_a2a_message(
            receiver="Router",
            content=f"I've identified the query topic as: {topic}",
            message_type="topic_identification",
            thread_id=str(state.get("metadata", {}).get("thread_id", uuid.uuid4()))
        )
        
        return {"topic": topic, **state}

    async def _run_router_node(self, state):
        """Run the router agent to determine which specialized agents to use."""
        thread_id = str(state.get("metadata", {}).get("thread_id", ""))
        
        # Process received messages from analyzer
        await self.router.process_received_messages(thread_id=thread_id)
        
        # Proceed with routing
        query = state["user_query"]
        topic = state["topic"]
        
        routing_prompt = f"Topic: {topic}\nQuery: {query}\n\nWhich specialized agents should handle this query?"
        routing_result = await self.router.process(routing_prompt)
        
        # Extract agent names from the routing result
        agent_names = self._parse_agent_names(routing_result)
        
        # Use A2A protocol to communicate with each selected agent
        for agent_name in agent_names:
            specialized_agent = self._get_agent_by_name(agent_name)
            if specialized_agent:
                await self.router.send_a2a_message(
                    receiver=agent_name,
                    content=f"Please process this query: {query}",
                    message_type="query_routing",
                    metadata={"topic": topic},
                    thread_id=thread_id
                )
        
        return {"selected_agents": agent_names, **state}

    async def _run_specialized_agent_node(self, state: AgentState) -> AgentState:
        """Run specialized agents to handle the query."""
        logger.info(f"Processing with agents: {state['selected_agents']}")
        
        # Initialize agent responses if not already there
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        
        # Process with each selected agent
        for agent_name in state["selected_agents"]:
            try:
                # Get the agent instance
                agent = self.agent_mapping.get(agent_name)
                if not agent:
                    logger.warning(f"Agent {agent_name} not found in agent mapping")
                    continue
                    
                # Process the query with this agent
                response = await agent.process(state["user_query"])
                
                # Add response to state
                state["agent_responses"][agent_name] = response
                
                # Record in conversation history
                state["conversation_history"].append({
                    "agent": agent_name,
                    "action": "process_query",
                    "result": response
                })
                
                # Add to context using MCP
                agent.add_context(
                    content=response,
                    context_type=f"{agent_name.lower()}_information",
                    importance=0.8
                )
                
            except Exception as e:
                logger.error(f"Error processing with agent {agent_name}: {str(e)}")
                logger.exception("Detailed traceback")
                # Add error response
                state["agent_responses"][agent_name] = f"Error: Could not process with {agent_name}"
        
        return state

    async def _run_evaluator_node(self, state):
        """Run the evaluator agent to determine if the responses are sufficient."""
        thread_id = str(state.get("metadata", {}).get("thread_id", ""))
        
        # Process all received messages from specialized agents
        await self.evaluator.process_received_messages(thread_id=thread_id)
        
        # Get all relevant context
        all_context = self.evaluator.get_relevant_contexts()
        
        # Evaluate completeness
        evaluation_prompt = f"""
        Query: {state['user_query']}
        Topic: {state['topic']}
        
        Gathered information:
        {all_context}
        
        Is this information sufficient to answer the query completely? 
        If yes, say "SUFFICIENT". 
        If not, explain what's missing and say "INSUFFICIENT".
        """
        
        evaluation_result = await self.evaluator.process(evaluation_prompt)
        
        # Inform synthesizer via A2A
        await self.evaluator.send_a2a_message(
            receiver="Synthesizer",
            content=evaluation_result,
            message_type="evaluation_result",
            thread_id=thread_id
        )
        
        is_sufficient = "SUFFICIENT" in evaluation_result.upper()
        
        return {"evaluation": evaluation_result, "is_sufficient": is_sufficient, **state}

    async def _run_synthesizer_node(self, state):
        """Synthesize the final response from all agent outputs."""
        thread_id = str(state.get("metadata", {}).get("thread_id", ""))
        
        # Process messages from evaluator
        await self.synthesizer.process_received_messages(thread_id=thread_id)
        
        # Get all relevant context
        all_context = self.synthesizer.get_relevant_contexts()
        
        synthesis_prompt = f"""
        Query: {state['user_query']}
        
        Information gathered:
        {all_context}
        
        Please synthesize a comprehensive, well-formatted answer to the query.
        """
        
        final_response = await self.synthesizer.process(synthesis_prompt)
        
        return {"final_response": final_response, **state}

from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import operator

# Define your state
class State(TypedDict):
    messages: List[Dict[str, Any]]
    next: str

# Create your graph
def create_graph():
    workflow = StateGraph(State)
    # Add nodes, edges, etc.
    # ...
    return workflow.compile()