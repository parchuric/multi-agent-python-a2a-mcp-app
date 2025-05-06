import { Agent } from './agent.interface';
import { callOpenAI } from '../api/openai';
import axios from 'axios';

export class NewsAgent implements Agent {
  private name = 'News Agent';
  private description = 'Provides breaking news and current events';
  private apiKey = process.env.NEWS_API_KEY || '';
  
  constructor() {}
  
  public getName(): string {
    return this.name;
  }
  
  public getDescription(): string {
    return this.description;
  }
  
  private async extractNewsTopics(query: string): Promise<{topic: string, subtopics: string[]}> {
    const response = await callOpenAI(
      `Extract the main news topic and any subtopics from this news-related query: "${query}"
      Return the answer in JSON format with these keys:
      - topic: the main topic of interest
      - subtopics: array of more specific aspects of the topic (empty array if none)
      
      Return ONLY valid JSON, nothing else.`
    );
    
    try {
      return JSON.parse(response);
    } catch (e) {
      return { topic: query, subtopics: [] };
    }
  }
  
  private async getNewsArticles(topic: string, count = 5): Promise<any[]> {
    try {
      // Using NewsAPI
      const response = await axios.get(
        `https://newsapi.org/v2/everything?q=${encodeURIComponent(topic)}&sortBy=publishedAt&pageSize=${count}&apiKey=${this.apiKey}`
      );
      
      return response.data.articles || [];
    } catch (error) {
      console.error('Error fetching news:', error);
      return [];
    }
  }
  
  private async getBreakingNews(category = 'general'): Promise<any[]> {
    try {
      // Get top headlines
      const response = await axios.get(
        `https://newsapi.org/v2/top-headlines?country=us&category=${category}&apiKey=${this.apiKey}`
      );
      
      return response.data.articles || [];
    } catch (error) {
      console.error('Error fetching breaking news:', error);
      return [];
    }
  }
  
  public async handleQuery(query: string): Promise<string> {
    try {
      // Check if query asks about breaking news
      const isBreakingNews = /breaking|latest|recent|today|update/i.test(query);
      
      let newsData = [];
      if (isBreakingNews) {
        newsData = await this.getBreakingNews();
      } else {
        // Extract topic from query
        const { topic } = await this.extractNewsTopics(query);
        newsData = await this.getNewsArticles(topic);
      }
      
      if (newsData.length === 0) {
        return `I'm sorry, I couldn't find any recent news articles related to your query. Would you like to try a different topic?`;
      }
      
      // Format news data for the prompt
      const formattedNewsData = newsData.map((article, index) => {
        return {
          title: article.title,
          source: article.source?.name || 'Unknown Source',
          publishedAt: article.publishedAt,
          description: article.description,
          url: article.url
        };
      });
      
      const response = await callOpenAI(
        `You are a news reporter presenting the most recent and relevant news. Create a helpful response to this query: "${query}"
        
        Use these REAL AND CURRENT news articles to inform your response:
        ${JSON.stringify(formattedNewsData)}
        
        Provide a summary of the most relevant articles.
        Include publication dates to emphasize how recent the information is.
        Cite sources for your information.
        If the query asks about something not covered in the articles, be honest about the limitation.
        Focus ONLY on answering the news question with the provided articles.`
      );
      
      return response;
    } catch (error: any) {
      console.error('Error in news agent:', error);
      return `Sorry, I couldn't retrieve news information at this time. Error: ${error.message}`;
    }
  }
}