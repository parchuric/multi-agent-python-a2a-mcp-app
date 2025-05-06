import { Agent } from './agent.interface';
import { callOpenAI } from '../api/openai';
import axios from 'axios';

export class SportsAgent implements Agent {
  private name = 'Sports Agent';
  private description = 'Provides up-to-date sports information and scores';
  private apiKey = process.env.SPORTS_API_KEY || '';
  
  constructor() {}
  
  public getName(): string {
    return this.name;
  }
  
  public getDescription(): string {
    return this.description;
  }
  
  private async extractSportsDetails(query: string): Promise<{sport: string, team?: string, league?: string}> {
    const response = await callOpenAI(
      `Extract the following information from this sports-related query: "${query}"
      Return the answer in JSON format with these keys:
      - sport: the sport type (e.g., basketball, football, soccer, etc.)
      - team: any specific team mentioned (or null if none)
      - league: any specific league mentioned (e.g., NBA, NFL, Premier League, etc.) (or null if none)
      
      Return ONLY valid JSON, nothing else.`
    );
    
    try {
      return JSON.parse(response);
    } catch (e) {
      return { sport: 'general' };
    }
  }
  
  private async getScores(sport: string, league?: string) {
    try {
      // Example using API-Sports
      const options = {
        headers: {
          'x-rapidapi-host': 'v3.football.api-sports.io',
          'x-rapidapi-key': this.apiKey
        }
      };
      
      let endpoint = '';
      if (sport === 'football' || sport === 'soccer') {
        endpoint = 'https://v3.football.api-sports.io/fixtures?live=all';
      } else if (sport === 'basketball') {
        endpoint = 'https://v3.basketball.api-sports.io/games?live=all';
      }
      
      if (endpoint) {
        const response = await axios.get(endpoint, options);
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error fetching sports data:', error);
      return null;
    }
  }
  
  private async getTeamInfo(sport: string, team: string) {
    // Implementation for team-specific info
    // Similar to getScores but with team filters
    return null;
  }
  
  public async handleQuery(query: string): Promise<string> {
    try {
      // Extract sports details from query
      const { sport, team, league } = await this.extractSportsDetails(query);
      
      let sportsData;
      if (team) {
        sportsData = await this.getTeamInfo(sport, team);
      } else {
        sportsData = await this.getScores(sport, league);
      }
      
      if (!sportsData) {
        // Fallback to news API for general sports information if no live data
        try {
          const newsResponse = await axios.get(
            `https://newsapi.org/v2/top-headlines?category=sports&q=${encodeURIComponent(sport)}&apiKey=${process.env.NEWS_API_KEY}`
          );
          sportsData = { type: 'news', data: newsResponse.data.articles.slice(0, 5) };
        } catch (e) {
          console.error('Error fetching sports news:', e);
        }
      }
      
      let promptData = 'No real-time sports data available.';
      if (sportsData) {
        promptData = JSON.stringify(sportsData);
      }
      
      const response = await callOpenAI(
        `You are a sports information specialist. Create a helpful response to this query: "${query}"
        
        Use this REAL-TIME sports data to inform your response:
        ${promptData}
        
        If you have live scores, include them prominently.
        If you only have news articles, summarize the most relevant ones.
        If you don't have specific data requested, be honest about the limitation.
        Focus ONLY on answering the sports question with the provided data.`
      );
      
      return response;
    } catch (error: any) {
      console.error('Error in sports agent:', error);
      return `Sorry, I couldn't retrieve sports information at this time. Error: ${error.message}`;
    }
  }
}