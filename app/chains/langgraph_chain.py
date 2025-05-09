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
        
        # Evaluate the responses
        evaluation = await self.evaluator.evaluate_responses(state["user_query"], state["agent_responses"])
        
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
        
        # Synthesize the final response
        final_response = await self.synthesizer.synthesize_responses(state["user_query"], state["agent_responses"])
        
        # Add the final response to state
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
        
        return state
    
    def _needs_more_info(self, state: AgentState) -> str:
        """Conditional edge function that determines if we need more information."""
        if state["needs_additional_info"] and state["current_agents"]:
            logger.info("Routing for additional information")
            return "needs_more_info"
        else:
            logger.info("Information is complete, proceeding to synthesis")
            return "complete"
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the entire workflow."""
        # Generate a thread ID for this conversation
        thread_id = str(uuid.uuid4())
        
        # Initialize the state
        initial_state = AgentState(
            user_query=query,
            identified_topic=None,
            agent_responses={},
            conversation_history=[],
            routing_decisions=[],
            current_agents=set(),
            needs_additional_info=False,
            final_response=None,
            errors=[],
            metadata={"thread_id": thread_id, "routing_attempts": 0}
        )
        
        # Run the workflow
        try:
            result = await self.workflow.ainvoke(initial_state)
            
            # Prepare the response
            response = {
                "query": query,
                "topic": result["identified_topic"],
                "agents_consulted": list(result["agent_responses"].keys()),
                "response": result["final_response"],
                "conversation_history": result["conversation_history"],
                "metadata": {
                    "thread_id": thread_id,
                    "a2a_message_count": len(self.a2a_handler.message_history),
                    "mcp_context_count": len(self.mcp_handler.contexts)
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            
            # Fallback to simple response using the analyzer agent
            try:
                # If we got to a point where we have some agent responses, use them
                if hasattr(initial_state, "agent_responses") and initial_state["agent_responses"]:
                    responses_text = ""
                    for agent, response in initial_state["agent_responses"].items():
                        responses_text += f"{agent}: {response}\n\n"
                    
                    fallback = await self.synthesizer.synthesize_responses(query, initial_state["agent_responses"])
                else:
                    # Otherwise use the news agent as a fallback
                    fallback = await self.news_agent.process_query(query)
                
                return {
                    "query": query,
                    "topic": initial_state.get("identified_topic", "unknown"),
                    "agents_consulted": ["FallbackAgent"],
                    "response": f"I encountered some difficulties while processing your request about AI technology news. Here's what I can tell you:\n\n{fallback}",
                    "error": str(e),
                    "metadata": {"error_handled": "true"}
                }
            except:
                # Last resort fallback
                return {
                    "query": query,
                    "error": str(e),
                    "response": "I'm sorry, I encountered an error while processing your query about AI technology news. Please try a more specific question or check back later."
                }

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