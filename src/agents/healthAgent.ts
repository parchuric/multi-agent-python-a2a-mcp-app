import { Agent } from './agent.interface';
import { callOpenAI } from '../api/openai';
import axios from 'axios';

export class HealthAgent implements Agent {
  private name = 'Health & Fitness Agent';
  private description = 'Provides general health and fitness information';
  private disclaimer = 'DISCLAIMER: This information is for general knowledge only and does not constitute professional medical advice. Please consult with qualified healthcare professionals for any health concerns or before making any decisions related to your health or treatment.';
  private apiKey = process.env.HEALTH_API_KEY || '';
  
  constructor() {}
  
  public getName(): string {
    return this.name;
  }
  
  public getDescription(): string {
    return this.description;
  }
  
  private async extractHealthTopic(query: string): Promise<{topic: string, subtopic?: string, isGeneral: boolean}> {
    const response = await callOpenAI(
      `Extract the health or fitness topic from this query: "${query}"
      Return the answer in JSON format with these keys:
      - topic: the main health or fitness topic (e.g., "nutrition", "exercise", "sleep", etc.)
      - subtopic: a more specific aspect if applicable (e.g., "protein intake", "cardio", "insomnia")
      - isGeneral: boolean indicating if this is a general question or specific health concern
      
      Return ONLY valid JSON, nothing else.`
    );
    
    try {
      return JSON.parse(response);
    } catch (e) {
      return { topic: 'general', isGeneral: true };
    }
  }
  
  private async getHealthArticles(topic: string): Promise<any[]> {
    try {
      // Using NewsAPI for health articles from reputable sources
      const response = await axios.get(
        `https://newsapi.org/v2/everything?q=${encodeURIComponent(topic)}+health+OR+fitness+OR+wellness&sortBy=relevancy&pageSize=5&domains=mayoclinic.org,nih.gov,medicalnewstoday.com,healthline.com&apiKey=${process.env.NEWS_API_KEY}`
      );
      
      return response.data.articles || [];
    } catch (error) {
      console.error('Error fetching health articles:', error);
      return [];
    }
  }
  
  private async getNutritionalData(food: string): Promise<any> {
    try {
      // Using USDA FoodData Central API
      const response = await axios.get(
        `https://api.nal.usda.gov/fdc/v1/foods/search?query=${encodeURIComponent(food)}&dataType=Foundation,SR%20Legacy&pageSize=1&api_key=${process.env.NUTRITION_API_KEY || this.apiKey}`
      );
      
      return response.data.foods[0] || null;
    } catch (error) {
      console.error(`Error fetching nutritional data for ${food}:`, error);
      return null;
    }
  }
  
  private async getExerciseData(exercise: string): Promise<any> {
    try {
      // Using an exercise API (example)
      const response = await axios.get(
        `https://api.api-ninjas.com/v1/exercises?name=${encodeURIComponent(exercise)}`,
        {
          headers: { 'X-Api-Key': process.env.EXERCISE_API_KEY || this.apiKey }
        }
      );
      
      return response.data[0] || null;
    } catch (error) {
      console.error(`Error fetching exercise data for ${exercise}:`, error);
      return null;
    }
  }
  
  public async handleQuery(query: string): Promise<string> {
    try {
      // Extract health topic from query
      const { topic, subtopic, isGeneral } = await this.extractHealthTopic(query);
      
      let healthData: any = { articles: [] };
      
      // Get information based on the topic
      if (topic === 'nutrition' || topic === 'food') {
        const foodItem = subtopic || topic;
        healthData.nutritionData = await this.getNutritionalData(foodItem);
      } else if (topic === 'exercise' || topic === 'workout' || topic === 'fitness') {
        const exerciseType = subtopic || topic;
        healthData.exerciseData = await this.getExerciseData(exerciseType);
      }
      
      // Always get some relevant articles as backup
      healthData.articles = await this.getHealthArticles(subtopic || topic);
      
      // Add sources to healthData
      healthData.sources = healthData.articles.map((article: any) => ({
        title: article.title,
        source: article.source?.name || 'Unknown Source',
        url: article.url
      }));
      
      // Ensure we alert if this might be medical advice
      const medicalAdviceWarning = !isGeneral ? 
        "Note that this query appears to be asking for specific medical advice. My response will be general information only." : "";
      
      const response = await callOpenAI(
        `You are a general health and fitness information provider. Create a helpful response to this query: "${query}"
        
        ${medicalAdviceWarning}
        
        Use this health and fitness information to inform your response:
        ${JSON.stringify(healthData)}
        
        For nutrition queries, include nutritional facts if available.
        For exercise queries, include proper form and benefit information if available.
        Cite reputable sources from the provided articles when possible.
        NEVER provide specific medical advice, diagnosis, or treatment recommendations.
        Always emphasize that this is general information only.
        Focus ONLY on answering the health/fitness question with the provided data.`
      );
      
      return `${response}\n\n${this.disclaimer}`;
    } catch (error: any) {
      console.error('Error in health agent:', error);
      return `Sorry, I couldn't retrieve health information at this time. Error: ${error.message}\n\n${this.disclaimer}`;
    }
  }
}