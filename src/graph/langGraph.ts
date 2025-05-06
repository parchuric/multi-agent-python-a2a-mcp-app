import { callOpenAI } from '../api/openai';
import { WeatherAgent } from '../agents/weatherAgent';
import { SportsAgent } from '../agents/sportsAgent';
import { NewsAgent } from '../agents/newsAgent';
import { StocksAgent } from '../agents/stocksAgent';
import { HealthAgent } from '../agents/healthAgent';
import { StateGraph, END, START } from '@langchain/langgraph'; // Add START import
import { RunnableConfig } from "langchain/schema/runnable";

// Define our state schema as a type
type AgentState = {
  query: string;
  topic: string | null;
  needsRerouting: boolean;
  agentResponses: Record<string, string>;
  finalResponse: string | null;
  currentAgent: string | null;
  history: Array<{
    role: 'user' | 'agent' | 'system';
    content: string;
    agent?: string;
  }>;
};

// Initialize our agents
const weatherAgent = new WeatherAgent();
const sportsAgent = new SportsAgent();
const newsAgent = new NewsAgent();
const stocksAgent = new StocksAgent();
const healthAgent = new HealthAgent();

// Define nodes for our graph
// 1. Query Analyzer Node - Determine the topic of the query
async function analyzerNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Analyzing query:", state.query);
  
  const response = await callOpenAI(
    `Determine which category the following question belongs to. 
    Respond with only one of these exact words: "weather", "sports", "news", "stocks", or "health".
    
    Question: ${state.query}
    
    Consider:
    - "weather" for questions about weather conditions, forecasts, etc.
    - "sports" for questions about games, teams, players, scores, etc.
    - "news" for questions about current events and breaking news.
    - "stocks" for questions about the stock market, investments, company financials, etc.
    - "health" for questions about fitness, wellness, health concerns, etc.`
  );
  
  // Extract just the category name from the response
  const cleanResponse = response.toLowerCase().trim();
  
  let topic = 'news'; // Default
  
  // Check if the response contains one of our categories
  if (cleanResponse.includes('weather')) topic = 'weather';
  else if (cleanResponse.includes('sports')) topic = 'sports';
  else if (cleanResponse.includes('news')) topic = 'news';
  else if (cleanResponse.includes('stocks')) topic = 'stocks';
  else if (cleanResponse.includes('health')) topic = 'health';
  
  console.log("Query categorized as:", topic);
  
  return {
    topic,
    history: [
      ...(state.history || []),
      { 
        role: 'system', 
        content: `Query categorized as: ${topic}` 
      }
    ]
  };
}

// 2. Agent Router Node - Route the query to the appropriate agent
async function routerNode(state: AgentState): Promise<Partial<AgentState>> {
  const topic = state.topic;
  console.log("Routing query to:", topic);
  
  return {
    currentAgent: topic,
    history: [
      ...(state.history || []),
      { 
        role: 'system', 
        content: `Routing query to ${topic} agent` 
      }
    ]
  };
}

// 3. Agent Execution Nodes - One for each specific agent
async function weatherNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Weather agent processing query:", state.query);
  const response = await weatherAgent.handleQuery(state.query);
  
  return {
    agentResponses: {
      ...(state.agentResponses || {}),
      weather: response
    },
    history: [
      ...(state.history || []),
      { 
        role: 'agent', 
        content: response,
        agent: 'weather'
      }
    ]
  };
}

async function sportsNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Sports agent processing query:", state.query);
  const response = await sportsAgent.handleQuery(state.query);
  
  return {
    agentResponses: {
      ...(state.agentResponses || {}),
      sports: response
    },
    history: [
      ...(state.history || []),
      { 
        role: 'agent', 
        content: response,
        agent: 'sports'
      }
    ]
  };
}

async function newsNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("News agent processing query:", state.query);
  const response = await newsAgent.handleQuery(state.query);
  
  return {
    agentResponses: {
      ...(state.agentResponses || {}),
      news: response
    },
    history: [
      ...(state.history || []),
      { 
        role: 'agent', 
        content: response,
        agent: 'news'
      }
    ]
  };
}

async function stocksNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Stocks agent processing query:", state.query);
  const response = await stocksAgent.handleQuery(state.query);
  
  return {
    agentResponses: {
      ...(state.agentResponses || {}),
      stocks: response
    },
    history: [
      ...(state.history || []),
      { 
        role: 'agent', 
        content: response,
        agent: 'stocks'
      }
    ]
  };
}

async function healthNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Health agent processing query:", state.query);
  const response = await healthAgent.handleQuery(state.query);
  
  return {
    agentResponses: {
      ...(state.agentResponses || {}),
      health: response
    },
    history: [
      ...(state.history || []),
      { 
        role: 'agent', 
        content: response,
        agent: 'health'
      }
    ]
  };
}

// 4. Response Evaluator Node - Check if we need to consult multiple agents
// Update the evaluatorNode function to prevent infinite loops
async function evaluatorNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Evaluating response quality and completeness");
  
  const currentAgentResponse = state.agentResponses?.[state.currentAgent || ''] || '';
  
  // Count how many times we've consulted each agent type to prevent loops
  const agentConsultationCount: Record<string, number> = {};
  state.history.forEach(entry => {
    if (entry.agent) {
      agentConsultationCount[entry.agent] = (agentConsultationCount[entry.agent] || 0) + 1;
    }
  });
  
  // If we've already consulted an agent more than twice, don't route back to it
  const maxConsultationsPerAgent = 2;
  const currentAgentConsultCount = agentConsultationCount[state.currentAgent || ''] || 0;
  
  // If we've already consulted too many agents or the same agent multiple times, force completion
  const totalConsultations = Object.values(agentConsultationCount).reduce((sum, count) => sum + count, 0);
  if (totalConsultations > 5 || currentAgentConsultCount >= maxConsultationsPerAgent) {
    console.log("Maximum agent consultations reached, synthesizing final response");
    return {
      needsRerouting: false,
      history: [
        ...(state.history || []),
        { 
          role: 'system', 
          content: `Maximum agent consultations reached, proceeding with synthesis` 
        }
      ]
    };
  }
  
  // Check if the response seems uncertain or needs additional context
  const evaluationPrompt = `
  Review this response to the user's query and determine if it needs additional information 
  from a different domain expert:
  
  User Query: ${state.query}
  Current Response (from ${state.currentAgent} agent): ${currentAgentResponse}
  
  Should this query be routed to another agent for additional information? 
  If yes, which ONE other agent would be most helpful (weather, sports, news, stocks, or health)?
  If no, just respond with "COMPLETE".
  
  Consider:
  - Only recommend routing to another agent if critical information is missing
  - We have already consulted: ${Object.keys(state.agentResponses || {}).join(', ')}
  - Each additional agent consultation adds processing time
  
  Answer with only "COMPLETE" or the name of the ONE other agent.
  `;
  
  const evaluation = await callOpenAI(evaluationPrompt);
  const cleanEvaluation = evaluation.trim().toLowerCase();
  
  let needsRerouting = false;
  let newAgent = null;
  
  if (cleanEvaluation !== 'complete' && 
      ['weather', 'sports', 'news', 'stocks', 'health'].includes(cleanEvaluation) &&
      cleanEvaluation !== state.currentAgent) {
    
    // Only allow rerouting if we haven't already consulted this agent too many times
    const targetAgentConsultCount = agentConsultationCount[cleanEvaluation] || 0;
    if (targetAgentConsultCount < maxConsultationsPerAgent) {
      needsRerouting = true;
      newAgent = cleanEvaluation;
      console.log(`Response needs additional information from ${newAgent} agent`);
    } else {
      console.log(`Would route to ${cleanEvaluation} agent, but already consulted ${targetAgentConsultCount} times`);
      needsRerouting = false;
    }
  } else {
    console.log("Response is complete");
    needsRerouting = false;
  }
  
  return {
    needsRerouting,
    currentAgent: needsRerouting ? newAgent : state.currentAgent,
    history: [
      ...(state.history || []),
      { 
        role: 'system', 
        content: needsRerouting ? 
          `Response needs additional information from ${newAgent} agent` : 
          `Response is complete` 
      }
    ]
  };
}

// 5. Response Synthesis Node - Combine responses if needed
async function synthesisNode(state: AgentState): Promise<Partial<AgentState>> {
  console.log("Synthesizing final response");
  
  // If we only have one agent response, use it directly
  if (Object.keys(state.agentResponses || {}).length === 1) {
    const agent = Object.keys(state.agentResponses || {})[0];
    return {
      finalResponse: state.agentResponses?.[agent],
      history: [
        ...(state.history || []),
        { 
          role: 'system', 
          content: `Using direct response from ${agent} agent` 
        }
      ]
    };
  }
  
  // Otherwise, synthesize a response from multiple agents
  const agentResponses = Object.entries(state.agentResponses || {})
    .map(([agent, response]) => `${agent.toUpperCase()} AGENT: ${response}`)
    .join('\n\n');
  
  const synthesisPrompt = `
  The user asked: "${state.query}"
  
  Different agents have provided the following responses:
  
  ${agentResponses}
  
  Create a unified, coherent answer that combines the relevant information from these responses.
  Make sure the answer is comprehensive but not repetitive.
  If there are any contradictions between the responses, acknowledge them and provide the most accurate information.
  `;
  
  const synthesizedResponse = await callOpenAI(synthesisPrompt);
  
  return {
    finalResponse: synthesizedResponse,
    history: [
      ...(state.history || []),
      { 
        role: 'system', 
        content: 'Synthesized response from multiple agents' 
      }
    ]
  };
}

// Helper function for router edges
function getNextAgentFromTopic(state: AgentState): string {
  return state.topic || "news";
}

// Helper function for evaluator edges
function getNextAgentFromEvaluation(state: AgentState): string {
  return state.needsRerouting ? (state.currentAgent || "news") : "synthesize";
}

// Helper for creating merging functions to satisfy the BinaryOperator requirement
function defaultMerger<T>() {
  return (a: T, b: T) => b;
}

// Create our workflow graph using the StateGraph from @langchain/langgraph
export const createAgentGraph = () => {
  // Create a new StateGraph instance with the correct constructor signature
  const graph = new StateGraph<AgentState>({
    channels: {
      query: { 
        value: defaultMerger<string>(),
        default: () => ""
      },
      topic: { 
        value: defaultMerger<string | null>(), 
        default: () => null
      },
      needsRerouting: { 
        value: defaultMerger<boolean>(),
        default: () => false
      },
      agentResponses: { 
        value: defaultMerger<Record<string, string>>(),
        default: () => ({})
      },
      finalResponse: { 
        value: defaultMerger<string | null>(),
        default: () => null
      },
      currentAgent: { 
        value: defaultMerger<string | null>(),
        default: () => null
      },
      history: { 
        value: defaultMerger<Array<{role: 'user' | 'agent' | 'system', content: string, agent?: string}>>(),
        default: () => []
      }
    }
  });
  
  // Add nodes
  graph.addNode("analyzer", analyzerNode);
  graph.addNode("router", routerNode);
  graph.addNode("weatherAgent", weatherNode);
  graph.addNode("sportsAgent", sportsNode);
  graph.addNode("newsAgent", newsNode);
  graph.addNode("stocksAgent", stocksNode);
  graph.addNode("healthAgent", healthNode);
  graph.addNode("evaluator", evaluatorNode);
  graph.addNode("synthesizer", synthesisNode);
  
  // Set START node as the entry point directly to analyzer
  graph.setEntryPoint("analyzer");
  
  // Add edges - no need to connect from START explicitly
  graph.addEdge("analyzer", "router");
  
  // Add conditional edges for the router
  graph.addConditionalEdges(
    "router",
    getNextAgentFromTopic,
    {
      "weather": "weatherAgent",
      "sports": "sportsAgent",
      "news": "newsAgent",
      "stocks": "stocksAgent",
      "health": "healthAgent"
    }
  );
  
  // Agent to evaluator connections
  graph.addEdge("weatherAgent", "evaluator");
  graph.addEdge("sportsAgent", "evaluator");
  graph.addEdge("newsAgent", "evaluator");
  graph.addEdge("stocksAgent", "evaluator");
  graph.addEdge("healthAgent", "evaluator");
  
  // Evaluator conditional edges
  graph.addConditionalEdges(
    "evaluator",
    getNextAgentFromEvaluation,
    {
      "weather": "weatherAgent",
      "sports": "sportsAgent",
      "news": "newsAgent",
      "stocks": "stocksAgent",
      "health": "healthAgent",
      "synthesize": "synthesizer"
    }
  );
  
  // Set the synthesizer as the end node
  graph.addEdge("synthesizer", END);
  
  // Compile the graph
  return graph.compile();
};

// Helper function to run a query through the agent graph
export async function processQuery(query: string): Promise<string> {
  try {
    const graph = createAgentGraph();
    
    // Set the initial state with the user's query
    const initialStateWithQuery: AgentState = {
      query,
      topic: null,
      needsRerouting: false,
      agentResponses: {},
      finalResponse: null,
      currentAgent: null,
      history: [{ role: 'user', content: query }]
    };
    
    // Run the graph with the correct config structure for recent versions
    const config: RunnableConfig = {};
    const result = await graph.invoke(initialStateWithQuery, config);
    
    // Return the final response
    return result.finalResponse || 'Sorry, I couldn\'t process your query.';
  } catch (error) {
    console.error('Error processing query with agent graph:', error);
    return 'Sorry, an error occurred while processing your query.';
  }
}