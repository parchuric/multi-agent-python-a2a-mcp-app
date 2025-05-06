# Multi-Agent Application

This project is a multi-agent application that leverages the LargeGraph framework and Azure OpenAI to provide answers across five topics: weather, sports, breaking news, the stock market, and fitness/healthcare. 

## Features

- **Intelligent Query Analysis**: Automatically categorizes user queries by topic
- **Specialized Agents**: Dedicated agents for weather, sports, news, stocks, and health
- **Collaborative Intelligence**: Agents can work together on complex queries
- **LangGraph Orchestration**: Uses LangGraph for advanced agent coordination
- **Anti-recursion Protection**: Prevents infinite loops between agents

## Architecture Components:
1. User Interface
Web Interface: The frontend that collects user queries and displays responses

2. API Layer
Express API: Handles HTTP requests, communicates with the LangGraph agent system

3. Agent Graph
Analyzer Node: Determines the topic category of the user query
Router Node: Directs the query to the appropriate specialized agent
Agent Nodes:
Weather Agent: Handles weather-related queries
Sports Agent: Processes sports-related information
News Agent: Provides current events information
Stocks Agent: Delivers financial market data
Health Agent: Answers health and wellness questions
Evaluator Node: Determines if additional information is needed from other agents
Synthesizer Node: Combines information from multiple agents when necessary

4. State Management
AgentState: Shared state object that tracks:
User query
Identified topic
Agent responses
Conversation history
Routing decisions

5. External Services
Azure OpenAI: For natural language understanding and generation
Domain-specific APIs: Weather, News, Sports, and Stocks data sources

## Flow of Information:

1. User sends a query through the web interface 
2. Express API receives the query and initializes the agent graph 
3. Analyzer node categorizes the query by topic 
4. Router directs the query to the appropriate specialized agent 
5. Agent processes the query, potentially calling external APIs 
6. Evaluator determines if the response is complete or needs input from other agents 
7. If more information is needed, query is routed to additional agents 
8. Synthesizer combines information from multiple agents when necessary 
9. Final response is returned to the API and displayed to the user 

This architecture leverages LangGraph's directed graph structure to create a workflow where specialized agents can collaborate on complex queries, with state being maintained throughout the entire process. 

1. **Query Analysis**: Determines the query's primary topic
2. **Agent Routing**: Directs the query to the appropriate specialized agent
3. **Response Evaluation**: Determines if additional agent input is needed
4. **Multi-agent Collaboration**: Consults additional agents when necessary
5. **Response Synthesis**: Combines information into a coherent answer

## Prerequisites

- Node.js v16+
- TypeScript
- Azure OpenAI API access
- Various API keys for agent services (see .env.example)


## Project Structure

```
multi-agent-app
├── src
│   ├── api
│   ├── agents
│   ├── graph
│   ├── services
│   ├── interfaces
│   ├── ui
│   └── index.ts
├── config
├── .env.example
├── package.json
├── tsconfig.json
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd multi-agent-app
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env` and fill in the required values.
   
4. Build the project: \`npm run build\`

5. Start the server: \`npm start\`

## API Endpoints

- POST /api/query - Submit a query to the multi-agent system
  - Request body: \`{ "query": "Your question here" }\`
  - Response: \`{ "response": "Agent's answer" }\`

## Usage

To start the application, run:
```
npm start
```

Visit `http://localhost:3000` in your web browser to access the user interface.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
