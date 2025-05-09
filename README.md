# Multi-Agent Python Application with A2A and MCP

This project demonstrates a multi-agent system using LangChain, with support for Google's Agent-to-Agent (A2A) protocol and Model Context Protocol (MCP).

## Overview

This multi-agent AI system can answer different types of questions by routing them to specialized agents. Think of it as a team of experts working together where:

One expert analyzes your question.
Another expert decides who should answer it.
Specialized experts (for weather, sports, news, stocks, or health) provide information.
Another expert evaluates if the answer is complete.
A final expert puts everything together in a nice response.

The agents communicate using the A2A protocol, and share contextual information using MCP.

Key Components and Flow

1. The Core Structure
The application is organized in these main parts:

app/
├── agents/            # The different AI experts
│   ├── analyzer_agent.py      # Understands what you're asking
│   ├── router_agent.py        # Decides which experts to consult
│   ├── weather_agent.py       # Weather specialist
│   ├── sports_agent.py        # Sports specialist
│   ├── news_agent.py          # News specialist
│   ├── stocks_agent.py        # Finance specialist
│   ├── health_agent.py        # Health specialist
│   ├── evaluator_agent.py     # Checks if answers are complete
│   └── synthesizer_agent.py   # Combines everything into a final answer
├── api/               # Web server parts
│   └── server.py              # Handles web requests
├── chains/            # Orchestration logic
│   └── langgraph_chain.py     # Controls the flow between agents
├── models/            # Data structures
│   └── state.py               # Keeps track of the conversation
├── utils/             # Helper tools
│   ├── a2a_protocol.py        # Helps agents communicate
│   └── mcp_protocol.py        # Helps share context between agents
└── main.py            # Starting point of the application

2. Information Flow
When you ask a question, here's what happens:

Your Question
You ask something like "What's the weather in Seattle?"
This gets sent to the Flask web server in server.py

Analysis Phase
The AnalyzerAgent looks at your question and identifies what it's about (weather, sports, etc.). It tags your question with a topic

Routing Phase
The RouterAgent receives the analyzed question
It decides which specialized agent(s) should handle your question
For "What's the weather in Seattle?", it would choose the WeatherAgent

Information Gathering Phase
The chosen specialized agent (e.g., WeatherAgent) processes your question
If it has API keys (like in your .env file), it fetches real data
Otherwise, it uses its knowledge to give the best answer it can

Evaluation Phase
The EvaluatorAgent checks if the answer is complete
If not, it might go back to the router to get more information

Synthesis Phase
The SynthesizerAgent takes all the collected information
It creates a well-formatted, complete answer
This final answer is returned to you

3. Special Communication Features
This system uses two special protocols:

A2A Protocol (Agent-to-Agent): Helps the agents communicate with each other effectively
MCP Protocol (Model Context Protocol): Helps share and maintain context throughout the conversation

4. How to Run the Application
Make sure you have Python installed
Set up environment variables in the .env file:
Azure OpenAI credentials (for the AI models)
Optional API keys for specialized data (news, stocks, etc.)
Run the application: python -m app.main
Access the web interface at http://localhost:3000
Ask questions through the web interface or API

5. Example Flow

Simple Flow Example:
You ask: "What's the weather like in Seattle today?"\
The analyzer identifies this as a weather-related question\
The router directs it to the weather agent\
The weather agent processes the question (using API data if available)\
The evaluator confirms the answer is complete\
The synthesizer formats a nice response about Seattle's weather\
You receive the answer in the web interface

Complex Flow Example with A2A and MCP:
You ask: "How might the rainy weather in Seattle affect the Seahawks game this weekend, and what impact could this have on related sports stocks?"\
The analyzer identifies multiple topics: weather, sports, and stocks\
The router decides to consult multiple specialized agents

Using A2A protocol:
The weather agent retrieves Seattle's forecast (rain predicted)\
The weather agent sends this context to the sports agent using A2A messaging\
The sports agent analyzes how rain affects Seahawks' performance\
The sports agent shares this analysis with the stocks agent\
The stocks agent evaluates potential market impacts on related companies

Using MCP protocol:
All agents maintain shared awareness of the conversation context\
The MCP handler ensures each agent knows what other agents have already addressed\
This prevents redundant information and creates coherent handoffs between agents\
The evaluator reviews the collective information and determines more details are needed about specific stocks\
The router sends the query back to the stocks agent for additional information\
The synthesizer combines weather data, sports analysis, and financial insights into a comprehensive response\
You receive an integrated answer that covers all aspects of your question\
This complex example demonstrates how A2A enables direct agent-to-agent communication for collaborative problem-solving, while MCP ensures all agents maintain awareness of the evolving conversation context.

## Setup

Clone the repository

Install dependencies:
pip install -r requirements.txt

Set up environment variables:

Copy .env.example to .env and fill in the required values, including:
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT_ID
Optional API keys for NEWS_API_KEY, STOCKS_API_KEY, etc.
Start the server:

API Endpoints
POST /api/query - Submit a query to the multi-agent system
Request body: { "query": "Your question here" }
Response: { "response": "Agent's answer" }
Usage


## Usage

To start the application, run:
python -m app.main


Visit `http://localhost:3000` in your web browser to access the user interface.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
