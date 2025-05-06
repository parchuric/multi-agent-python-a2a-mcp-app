# Multi-Agent Application

This project is a multi-agent application that leverages the LargeGraph framework and Azure OpenAI to provide answers across five topics: weather, sports, breaking news, the stock market, and fitness/healthcare. 

## Features

- **Intelligent Query Analysis**: Automatically categorizes user queries by topic
- **Specialized Agents**: Dedicated agents for weather, sports, news, stocks, and health
- **Collaborative Intelligence**: Agents can work together on complex queries
- **LangGraph Orchestration**: Uses LangGraph for advanced agent coordination
- **Anti-recursion Protection**: Prevents infinite loops between agents

## Architecture

The system uses a directed graph to orchestrate the flow of information:

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