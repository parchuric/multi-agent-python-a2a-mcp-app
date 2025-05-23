# Multi-Agent Python Application with A2A, MCP and LangGraph

This project demonstrates a multi-agent system using LangGraph, with support for Google's Agent-to-Agent (A2A) protocol and Model Context Protocol (MCP).

## Overview

This multi-agent AI system can answer different types of questions by routing them to specialized agents. Think of it as a team of experts working together where:

- One expert analyzes your question
- Another expert decides who should answer it
- Specialized experts (for weather, sports, news, stocks, or health) provide information
- Another expert evaluates if the answer is complete
- A final expert puts everything together in a nice response

The agents communicate using the A2A protocol, and share contextual information using MCP.

## Overview

This multi-agent AI system can answer different types of questions by routing them to specialized agents...

## System Architecture

<!-- Markdown image syntax version (commented out)
![Architecture Diagram](images/MultiAgentArchitecture.png)
-->
<img src="images/MultiAgentArchitecture.png" width="800" alt="Architecture Diagram">
*Figure 1: Detailed architecture of the multi-agent system with A2A and MCP protocols*


The architecture diagram above illustrates the flow of information through the multi-agent system:
   
   1. **User Layer**: The user interacts with the web interface to submit queries and receive responses.
   
   2. **Application Layer**: The API server and main application handle HTTP requests and orchestrate the overall system.
   
   3. **LangGraph Orchestration**: The LangGraph component manages the workflow between agents, determining which agents to invoke and when.
   
   4. **Agent Layer**: Multiple specialized agents process different aspects of the query:
      - The Analyzer Agent identifies query topics and entities
      - The Router Agent directs queries to appropriate specialized agents
      - Domain-specific agents (Weather, Sports, News, Stocks, Health) provide expert knowledge
      - The Evaluator Agent assesses response completeness
      - The Synthesizer Agent combines information into cohesive responses
   
   5. **Communication Protocols**:
      - **A2A Protocol**: Enables direct agent-to-agent messaging for collaboration
      - **MCP Protocol**: Provides shared context across agents to maintain coherent understanding
   
   6. **External Integration**: Specialized agents connect to external APIs when needed to fetch real-time data.
   
   This architecture enables sophisticated multi-agent collaboration, with agents working together to provide comprehensive answers to complex, multi-domain questions.

## Key Components and Flow

### 1. The Core Structure

The application is organized in these main parts:

      app/
      ├── agents/            # The different AI experts\
      │   ├── analyzer_agent.py      # Understands what you're asking\
      │   ├── router_agent.py        # Decides which experts to consult\
      │   ├── weather_agent.py       # Weather specialist\
      │   ├── sports_agent.py        # Sports specialist\
      │   ├── news_agent.py          # News specialist\
      │   ├── stocks_agent.py        # Finance specialist\
      │   ├── health_agent.py        # Health specialist\
      │   ├── evaluator_agent.py     # Checks if answers are complete\
      │   └── synthesizer_agent.py   # Combines everything into a final answer\
      ├── api/               # Web server parts\
      │   └── server.py              # Handles web requests\
      ├── chains/            # Orchestration logic\
      │   └── langgraph_chain.py     # Controls the flow between agents\
      ├── models/            # Data structures\
      │   └── state.py               # Keeps track of the conversation\
      ├── utils/             # Helper tools\
      │   ├── a2a_protocol.py        # Helps agents communicate\
      │   └── mcp_protocol.py        # Helps share context between agents\
      └── main.py            # Starting point of the application

2. **Information Flow**
      When you ask a question, here's what happens:
      
      **Your Question** \
      You ask something like "What's the weather in Seattle?"\
      This gets sent to the Flask web server in server.py
      
      **Analysis Phase** \
      The AnalyzerAgent looks at your question and identifies what it's about (weather, sports, etc.). It tags your question with a topic
      
      **Routing Phase** \
      The RouterAgent receives the analyzed question\
      It decides which specialized agent(s) should handle your question\
      For "What's the weather in Seattle?", it would choose the WeatherAgent
      
      **Information Gathering Phase** \
      The chosen specialized agent (e.g., WeatherAgent) processes your question\
      If it has API keys (like in your .env file), it fetches real data\
      Otherwise, it uses its knowledge to give the best answer it can
      
      **Evaluation Phase** \
      The EvaluatorAgent checks if the answer is complete\
      If not, it might go back to the router to get more information
      
      **Synthesis Phase** \
      The SynthesizerAgent takes all the collected information\
      It creates a well-formatted, complete answer\
      This final answer is returned to you

3. **Special Communication Features** \
This system uses two special protocols:

A2A Protocol (Agent-to-Agent): Helps the agents communicate with each other effectively\
****#** A2A Protocol Implementation in the Multi-Agent System******

The Agent-to-Agent (A2A) protocol is implemented in this project to enable direct communication between specialized agents, allowing them to collaborate more effectively on complex queries. Here's a detailed explanation of how it works:

   ## 1. Core A2A Components

   ### A2A Handler
   The core implementation of the A2A protocol is in a2a_protocol.py, which defines:

   - A message structure for agent communication
      - Functions to send/receive messages between agents
      - Thread management to maintain conversation context

      ### BaseAgent Integration
      The `BaseAgent` class serves as the foundation for all specialized agents and includes A2A functionality:

      - Each agent is initialized with an `a2a_handler` that connects to the A2A messaging system
      - The `send_a2a_message` method allows an agent to send messages to other agents
      - The `process_received_messages` method processes incoming messages from other agents

      ## 2. Message Flow Process

      When an agent needs to communicate with another agent:

      1. The sender agent calls `send_a2a_message` with:
         - The receiver agent's name
         - Message content
         - Message type (e.g., "query", "response", "information")
         - Optional thread ID to maintain conversation context
         - Optional metadata

      2. The A2A handler:
         - Creates a message object with sender, receiver, content, and metadata
         - Stores the message in a message queue with thread identification
         - Manages message ordering and priority

      3. The receiver agent later calls `process_received_messages`:
         - Retrieves all messages addressed to itself
         - Processes each message based on type and content
         - Formulates responses if needed
         - Optionally sends responses back to the original sender

      ## 3. Integration with LangGraph Workflow

      The A2A protocol is integrated into the LangGraph workflow in langgraph_chain.py:

      1. **In the Analysis Phase:**
         - The analyzer agent identifies topics and entities
         - Uses A2A to send topic information to the router

      2. **In the Routing Phase:**
         - The router determines which specialized agents to use
         - Uses A2A to send specific queries to each selected agent

      3. **In the Information Gathering Phase:**
         - Specialized agents process their specific queries
         - Use A2A to share findings with other agents when relevant
         - For example, the weather agent might share weather data with the sports agent

      4. **In the Evaluation Phase:**
         - The evaluator checks responses for completeness
         - Uses A2A to request additional information if needed

      5. **In the Synthesis Phase:**
         - The synthesizer receives inputs from all agents through A2A
         - Combines all information into a cohesive response

      ## 4. Example A2A Interaction Flow

      For the complex example in this README:

      1. User asks: "How might the rainy weather in Seattle affect the Seahawks game this weekend, and what impact could this have on related sports stocks?"

      2. Analysis & Routing:
         ```python
         # Analyzer identifies topics and sends to router via A2A
         await analyzer.send_a2a_message(
            receiver="Router",
            content="Query involves weather, sports, and stocks topics",
            message_type="topic_identification",
            thread_id=thread_id
         )
         ```

      3. Weather Agent Processing:
         ```python
         # Weather agent gets information and shares with sports agent
         weather_data = "Rain predicted in Seattle: 80% chance of precipitation..."
         await weather_agent.send_a2a_message(
            receiver="SportsAgent",
            content=weather_data,
            message_type="weather_information",
            metadata={"location": "Seattle", "day": "Sunday"},
            thread_id=thread_id
         )
         ```

      4. Sports Agent Processing:
         ```python
         # Sports agent processes weather data
           await sports_agent.process_received_messages(thread_id=thread_id)
         
         # Shares analysis with stocks agent
         sports_analysis = "Rain typically reduces Seahawks' passing effectiveness by 15%..."
         await sports_agent.send_a2a_message(
            receiver="StocksAgent",
            content=sports_analysis,
            message_type="sports_analysis",
            metadata={"team": "Seahawks", "weather_impact": "high"},
            thread_id=thread_id
         )
         ```

      5. Stocks Agent Processing:
         ```python
         # Stocks agent processes weather and sports information
         await stocks_agent.process_received_messages(thread_id=thread_id)
         
         # Generates financial analysis based on combined information
         stocks_analysis = "Companies like Nike (NKE) and DraftKings (DKNG) may see..."
         ```

      ## 5. Advantages of A2A in this System

      1. **Direct Communication:** Agents can communicate directly without going through a central coordinator for every interaction

      2. **Specialized Knowledge Transfer:** Domain-specific insights can be shared between agents (like weather affecting sports)

      3. **Reduced Redundancy:** Agents can build on each other's work rather than repeating queries or analysis

      4. **Flexible Workflow:** Allows for dynamic, non-linear processing paths based on the specific query needs

      The A2A protocol essentially creates a network of collaborating agents rather than a rigid pipeline, enabling more sophisticated reasoning and information sharing throughout the multi-agent system. 


   
MCP Protocol (Model Context Protocol): Helps share and maintain context throughout the conversation. In this multi-agent Python application, the Model Context Protocol (MCP) is implemented with distinct components that represent the MCP host, client, and server. Let us break down how these roles are assigned in the application:

## MCP Components Overview

   ### 1. Model Host
   In MCP terminology, the **Model Host** is the component that provides access to the underlying language model and manages its context.

   **In this application**:
      - The Azure OpenAI integration serves as the Model Host
      - It's typically initialized in the `main.py` file
      - This component manages connections to the Azure OpenAI API and provides the foundation LLM capabilities

   ### 2. MCP Server
   The **MCP Server** manages the context for conversations and interactions between agents.

   **In this application**:
      - The `mcp_protocol.py` in the `utils` folder contains an MCP server implementation
      - This component stores and manages shared context between different agent interactions
      - It creates a central "memory" that persists throughout the conversation flow

   ### 3. MCP Client
   **MCP Clients** are components that connect to the MCP Server to access and modify the shared context.

   **In this application**:
      - Each specialized agent (weather, sports, news, etc.) acts as an MCP Client
      - The `mcp_handler` parameter passed to each agent connects them to the MCP infrastructure
      - Agents use this handler to retrieve context about what other agents have already processed

## How They Work Together

Here's the flow of how these components interact:

   1. **Initialization**:
      - The Model Host (Azure OpenAI integration) is set up in `main.py`
      - An MCP Server instance is created to manage shared context
      - MCP Clients (handlers) are created for each agent

      2. **During Query Processing**:
      - When a query enters the system, the Model Host provides LLM capabilities
      - The MCP Server maintains the evolving conversation context
      - Each agent (as an MCP Client) can:
      - Read the shared context to understand what's already known
      - Update the shared context with new information
      - Use the context to avoid redundant work

      3. **Example in Complex Queries**:
      - For a multi-topic query like "How will weather affect the Seahawks game and related stocks?"
      - The weather agent processes weather information and adds it to the MCP context
      - The sports agent reads the weather context and adds sports analysis
      - The stocks agent reads both weather and sports context to provide financial insights
      - This coordination happens through the MCP Server's shared context management
  
This architecture allows agents to share context efficiently, building on each other's knowledge throughout the conversation flow.

     
 5. **How to Run the Application** \
      Make sure you have Python installed\
      Set up environment variables in the .env file:\
      Azure OpenAI credentials (for the AI models)\
      Optional API keys for specialized data (news, stocks, etc.)\
      Run the application: python -m app.main\
      Access the web interface at http://localhost:3000\
      Ask questions through the web interface or API

6. **Example Flow** 

**Simple Flow Example:** \
      You ask: \"What's the weather like in Seattle today?"\
      The analyzer identifies this as a weather-related question\
      The router directs it to the weather agent\
      The weather agent processes the question (using API data if available)\
      The evaluator confirms the answer is complete\
      The synthesizer formats a nice response about Seattle's weather\
      You receive the answer in the web interface

**Complex Flow Example with A2A and MCP:** \
      You ask: \
"How might the rainy weather in Seattle affect the Seahawks game this weekend, and what impact could this have on related sports stocks?"\
The analyzer identifies multiple topics: weather, sports, and stocks\
The router decides to consult multiple specialized agents

**Using A2A protocol:** \
The weather agent retrieves Seattle's forecast (rain predicted)\
The weather agent sends this context to the sports agent using A2A messaging\
The sports agent analyzes how rain affects Seahawks' performance\
The sports agent shares this analysis with the stocks agent\
The stocks agent evaluates potential market impacts on related companies


**Using MCP protocol:**
\
All agents maintain shared awareness of the conversation context\
The MCP handler ensures each agent knows what other agents have already addressed\
This prevents redundant information and creates coherent handoffs between agents\
The evaluator reviews the collective information and determines more details are needed about specific stocks\
The router sends the query back to the stocks agent for additional information\
The synthesizer combines weather data, sports analysis, and financial insights into a comprehensive response\
You receive an integrated answer that covers all aspects of your question\
This complex example demonstrates how A2A enables direct agent-to-agent communication for collaborative problem-solving, while MCP ensures all agents maintain awareness of the evolving conversation context.


# LangGraph Implementation in the Multi-Agent System

LangGraph serves as the orchestration framework for the multi-agent workflow in this project, providing a structured way to manage the flow of information between different specialized agents. Here's how it's implemented:

## Core LangGraph Components

### 1. Graph Definition and State Management

The implementation is primarily in [`app/chains/langgraph_chain.py`](app/chains/langgraph_chain.py ), which defines:

- A state class that tracks the conversation flow
- Node functions for each processing step
- Edge functions that determine the routing between nodes
- Conditional logic for agent selection

```python
class MultiAgentLangGraph:
    def __init__(self, llm, specialized_agents=None):
        self.llm = llm
        self.specialized_agents = specialized_agents or []
        # Initialize agents and build the workflow graph
        self._build_graph()
```

### 2. Node Functions

LangGraph uses node functions to represent different processing stages:

```python
async def _analyze_query_node(self, state: AgentState) -> AgentState:
    """Node function for analyzing the query."""
    # Analyzer determines topic and entities
    
async def _route_query_node(self, state: AgentState) -> AgentState:
    """Node function for routing the query to specialized agents."""
    # Router selects which agents should handle the query
    
async def _run_specialized_agent_node(self, state: AgentState) -> AgentState:
    """Node function for running specialized agents."""
    # Selected agents process the query
    
async def _evaluate_completeness_node(self, state: AgentState) -> AgentState:
    """Node function for evaluating response completeness."""
    # Evaluator checks if more information is needed
    
async def _synthesize_responses(self, state: AgentState) -> AgentState:
    """Node function for synthesizing the final response."""
    # Synthesizer creates the final response
```

### 3. Graph Construction

The workflow is assembled using LangGraph's builder pattern:

```python
def _build_graph(self):
    """Build the LangGraph workflow."""
    # Define the graph structure
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("analyze_query", self._analyze_query_node)
    builder.add_node("route_query", self._route_query_node)
    builder.add_node("run_specialized_agents", self._run_specialized_agent_node)
    builder.add_node("evaluate_completeness", self._evaluate_completeness_node)
    builder.add_node("synthesize", self._synthesize_responses)
    
    # Add edges (connections between nodes)
    builder.add_edge("analyze_query", "route_query")
    builder.add_edge("route_query", "run_specialized_agents")
    builder.add_edge("run_specialized_agents", "evaluate_completeness")
    
    # Add conditional edge based on completeness
    builder.add_conditional_edges(
        "evaluate_completeness",
        self._is_information_complete,
        {
            True: "synthesize",
            False: "route_query"  # Loop back if more info needed
        }
    )
    
    # Set the entry and exit points
    builder.set_entry_point("analyze_query")
    builder.set_finish_point("synthesize")
    
    # Compile the workflow
    self.workflow = builder.compile()
```

### 4. State Management

The `AgentState` class (defined in [`app/models/state.py`](app/models/state.py )) maintains the conversation state throughout the workflow:

```python
class AgentState(TypedDict):
    user_query: str  # The original user question
    topic: Optional[str]  # Identified topic (weather, sports, etc.)
    selected_agents: List[str]  # Which specialized agents to use
    agent_responses: Dict[str, str]  # Responses from each agent
    needs_more_info: bool  # Whether more information is needed
    final_response: Optional[str]  # The synthesized response
    conversation_history: List[Dict]  # History of agent interactions
    metadata: Dict  # Additional metadata like thread_id
```

## Integration with A2A and MCP

LangGraph serves as the orchestration layer that works with both A2A and MCP:

1. **A2A Integration**:
   - Each node function can use A2A to send messages between agents
   - For example, the router sends queries to specialized agents via A2A

2. **MCP Integration**:
   - The graph maintains a shared context accessible across nodes
   - Each agent can access and update this shared context

## Execution Flow

When a query is processed:

1. The workflow starts at the entry point (`analyze_query`)
2. Each node processes the state and passes it to the next node
3. Conditional edges route the flow based on evaluation results
4. The workflow completes when it reaches the finish point (`synthesize`)

```python
async def process_query(self, query: str) -> str:
    """Process a query through the multi-agent workflow."""
    # Initialize thread ID for this conversation
    thread_id = str(uuid.uuid4())
    
    # Initialize state
    initial_state = {
        "user_query": query,
        "conversation_history": [],
        "metadata": {
            "thread_id": thread_id
        }
    }
    
    # Run the graph
    final_state = await self.workflow.ainvoke(initial_state)
    
    # Return the final response
    return final_state["final_response"]
```

## Benefits of LangGraph in this Application

1. **Structured Workflow**: Provides a clear, visual representation of the agent interaction flow
2. **Conditional Logic**: Enables dynamic routing based on conversation state
3. **State Persistence**: Maintains context throughout the multi-agent interaction
4. **Parallelization**: Can run multiple agents simultaneously when needed
5. **Looping**: Supports iterative refinement of responses when more information is needed

This implementation of LangGraph creates a flexible, extensible system where specialized agents can work together to answer complex, multi-domain questions while maintaining coherent conversation flow and context.

## Token Usage and Cost Tracking

The application includes a comprehensive token tracking system that monitors API usage and calculates costs when interacting with Azure OpenAI services.

### Features

- **Real-time Token Counting**: Tracks prompt tokens, completion tokens, and total tokens for each API call
- **Agent-specific Metrics**: Breaks down token usage by individual agents in the system
- **Cost Estimation**: Calculates approximate costs based on current Azure OpenAI pricing
- **Usage Reporting**: Provides both API endpoint and console reporting of token usage

### Usage Report Example
==== Token Usage Report ==== Total API Calls: 24 Total Prompt Tokens: 4,382 Total Completion Tokens: 1,217 Total Tokens: 5,599 Estimated Cost: $0.0254 ($0.0131 input + $0.0123 output)

==== Usage by Agent ====

Agent: AnalyzerAgent API Calls: 6 Prompt Tokens: 1,245 Completion Tokens: 298 Total Tokens: 1,543 Estimated Cost: $0.0068

Agent: RouterAgent API Calls: 6 Prompt Tokens: 854 Completion Tokens: 187 Total Tokens: 1,041 Estimated Cost: $0.0047

Agent: WeatherAgent API Calls: 4 Prompt Tokens: 728 Completion Tokens: 336 Total Tokens: 1,064 Estimated Cost: $0.0042


### How to Access Token Usage Data

1. **Web Interface**: Visit the `/usage-report` endpoint in your browser

http://localhost:3000/usage-report


2. **Console Output**: Token usage is printed to the console when the application exits

3. **Log Files**: Detailed logs are saved in the `logs/token_usage.json` file

### Implementation Details

The token tracking middleware wraps the Azure OpenAI client to intercept and record all API calls. The implementation:

- Uses the `token_counter.py` class to track all LLM interactions
- Preserves which agent made each call for accurate attribution
- Handles various response formats to reliably extract token counts
- Persists usage data to disk for later analysis

This feature helps monitor API usage costs and optimize prompts for better efficiency.

## Setup 

Clone the repository

Install dependencies:
pip install -r requirements.txt

Set up environment variables:

Copy .env.example to .env and fill in the required values, including: \
AZURE_OPENAI_ENDPOINT \
AZURE_OPENAI_API_KEY \
AZURE_OPENAI_DEPLOYMENT_ID \
Optional API keys for NEWS_API_KEY, STOCKS_API_KEY, etc. \
Start the server:

API Endpoints
\
POST /api/query - Submit a query to the multi-agent system
Request body: { "query": "Your question here" }
Response: { "response": "Agent's answer" }



## Usage

To start the application, run:
python -m app.main


Visit `http://localhost:3000` in your web browser to access the user interface.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
