import { Agent } from './agent.interface';
import { callOpenAI } from '../api/openai';
import axios from 'axios';

export class WeatherAgent implements Agent {
  private name = 'Weather Agent';
  private description = 'Provides information about weather conditions and forecasts';
  private apiKey = process.env.WEATHER_API_KEY || '';
  
  constructor() {}
  
  public getName(): string {
    return this.name;
  }
  
  public getDescription(): string {
    return this.description;
  }
  
  // Add a method to extract location with context awareness
  private async extractLocation(query: string, conversationContext?: Array<any>): Promise<string> {
    try {
      let contextPrompt = '';
      if (conversationContext && conversationContext.length > 0) {
        contextPrompt = `
        Previous conversation context:
        ${conversationContext.map(msg => `${msg.role}: ${msg.content}`).join('\n')}
        
        Based on this conversation context and the current query, `;
      }
      
      const response = await callOpenAI(
        `${contextPrompt}extract the location mentioned in this weather query. 
        If no specific location is mentioned, either:
        1. Infer the location from context if possible, or
        2. Return "unknown" if no location can be determined.
        
        Query: "${query}"
        
        Return ONLY the location name, nothing else.`
      );
      
      return response.trim();
    } catch (error) {
      console.error('Error extracting location:', error);
      return 'unknown';
    }
  }
  
  // Enhanced method to get weather data
  private async getWeatherData(location: string): Promise<any> {
    if (!this.apiKey || location === 'unknown') {
      return null;
    }
    
    try {
      const response = await axios.get(
        `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(location)}&appid=${this.apiKey}&units=metric`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching weather data for ${location}:`, error);
      return null;
    }
  }
  
  // Enhanced method to get forecast data
  private async getForecastData(location: string): Promise<any> {
    if (!this.apiKey || location === 'unknown') {
      return null;
    }
    
    try {
      const response = await axios.get(
        `https://api.openweathermap.org/data/2.5/forecast?q=${encodeURIComponent(location)}&appid=${this.apiKey}&units=metric`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching forecast data for ${location}:`, error);
      return null;
    }
  }
  
  // Enhanced handleQuery method with context support
  public async handleQuery(query: string, conversationContext?: Array<any>): Promise<string> {
    try {
      // Extract location with context awareness
      const location = await this.extractLocation(query, conversationContext);
      
      if (location === 'unknown') {
        return 'I need to know which location you\'re asking about to provide weather information. Could you please specify a city or region?';
      }
      
      // Get weather and forecast data
      const weatherData = await this.getWeatherData(location);
      const forecastData = await this.getForecastData(location);
      
      if (!weatherData) {
        return `I'm sorry, I couldn't find weather data for "${location}". Please check the location name and try again.`;
      }
      
      // Structure the data for the prompt
      const weatherInfo = {
        location: weatherData.name,
        country: weatherData.sys.country,
        current: {
          temperature: weatherData.main.temp,
          feels_like: weatherData.main.feels_like,
          humidity: weatherData.main.humidity,
          pressure: weatherData.main.pressure,
          description: weatherData.weather[0].description,
          wind: {
            speed: weatherData.wind.speed,
            direction: weatherData.wind.deg
          }
        },
        forecast: forecastData ? 
          forecastData.list.slice(0, 5).map((item: any) => ({
            time: item.dt_txt,
            temperature: item.main.temp,
            description: item.weather[0].description,
            humidity: item.main.humidity
          })) 
          : null
      };
      
      // Context-aware response generation
      let contextPrompt = '';
      if (conversationContext && conversationContext.length > 0) {
        contextPrompt = `
        Previous conversation context:
        ${conversationContext.map(msg => `${msg.role}: ${msg.content}`).join('\n')}
        
        Based on this conversation context and the current query, `;
      }
      
      const response = await callOpenAI(
        `${contextPrompt}You are a weather information specialist. Create a helpful, conversational response to this query: "${query}".
        
        Use this REAL-TIME weather data to inform your response:
        ${JSON.stringify(weatherInfo, null, 2)}
        
        Include specific numbers from the data such as temperature, conditions, humidity, etc.
        Format temperatures nicely (e.g., "22°C/72°F").
        If forecast data is available, include relevant forecast information.
        Focus ONLY on answering the weather question with the provided data.`
      );
      
      return response;
    } catch (error: any) {
      console.error('Error in weather agent:', error);
      return `Sorry, I couldn't retrieve weather information at this time. Error: ${error.message}`;
    }
  }
}

export default WeatherAgent;