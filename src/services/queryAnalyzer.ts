import { callOpenAI } from '../api/openai';

export async function analyzeQuery(query: string): Promise<string> {
  try {
    const response = await callOpenAI(
      `Determine which category the following question belongs to. 
      Respond with only one of these exact words: "weather", "sports", "news", "stocks", or "health".
      
      Question: ${query}
      
      Consider:
      - "weather" for questions about weather conditions, forecasts, etc.
      - "sports" for questions about games, teams, players, scores, etc.
      - "news" for questions about current events and breaking news.
      - "stocks" for questions about the stock market, investments, company financials, etc.
      - "health" for questions about fitness, wellness, health concerns, etc.`
    );
    
    // Extract just the category name from the response
    const cleanResponse = response.toLowerCase().trim();
    
    // Check if the response contains one of our categories
    if (cleanResponse.includes('weather')) return 'weather';
    if (cleanResponse.includes('sports')) return 'sports';
    if (cleanResponse.includes('news')) return 'news';
    if (cleanResponse.includes('stocks')) return 'stocks';
    if (cleanResponse.includes('health')) return 'health';
    
    // Default fallback
    return 'news';
  } catch (error) {
    console.error('Error analyzing query:', error);
    return 'news'; // Default to news if analysis fails
  }
}