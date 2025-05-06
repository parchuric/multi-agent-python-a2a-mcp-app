import { Agent } from './agent.interface';
import { callOpenAI } from '../api/openai';
import axios from 'axios';

export class StocksAgent implements Agent {
  private name = 'Stocks Agent';
  private description = 'Provides real-time stock market information';
  private apiKey = process.env.STOCKS_API_KEY || '';
  
  constructor() {}
  
  public getName(): string {
    return this.name;
  }
  
  public getDescription(): string {
    return this.description;
  }
  
  private async extractStocksInfo(query: string): Promise<{symbols: string[], timeframe: string, dataType: string}> {
    const response = await callOpenAI(
      `Extract the following information from this stock market query: "${query}"
      Return the answer in JSON format with these keys:
      - symbols: array of stock symbols or company names mentioned (convert company names to likely ticker symbols)
      - timeframe: the time period of interest (e.g., "today", "this week", "1 year", etc.) or "current" if not specified
      - dataType: what kind of data is being requested ("price", "trend", "news", "performance", "recommendation", etc.)
      
      Return ONLY valid JSON, nothing else.`
    );
    
    try {
      return JSON.parse(response);
    } catch (e) {
      return { symbols: [], timeframe: 'current', dataType: 'price' };
    }
  }
  
  private async getStockPrice(symbol: string): Promise<any> {
    try {
      // Using Alpha Vantage API
      const response = await axios.get(
        `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${this.apiKey}`
      );
      
      return response.data["Global Quote"] || null;
    } catch (error) {
      console.error(`Error fetching stock price for ${symbol}:`, error);
      return null;
    }
  }
  
  private async getStockHistory(symbol: string, timeframe: string): Promise<any> {
    try {
      let interval = 'daily';
      if (timeframe.includes('hour') || timeframe.includes('minute')) {
        interval = 'intraday';
      } else if (timeframe.includes('week')) {
        interval = 'weekly';
      } else if (timeframe.includes('month')) {
        interval = 'monthly';
      }
      
      const response = await axios.get(
        `https://www.alphavantage.co/query?function=TIME_SERIES_${interval.toUpperCase()}&symbol=${symbol}&apikey=${this.apiKey}`
      );
      
      // Extract the relevant time series data
      const timeSeriesKey = `Time Series (${interval.charAt(0).toUpperCase() + interval.slice(1)})`;
      return response.data[timeSeriesKey] || null;
    } catch (error) {
      console.error(`Error fetching stock history for ${symbol}:`, error);
      return null;
    }
  }
  
  private async getStockNews(symbols: string[]): Promise<any[]> {
    try {
      const symbolsString = symbols.join(',');
      // Using Alpha Vantage News API
      const response = await axios.get(
        `https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=${symbolsString}&apikey=${this.apiKey}`
      );
      
      return response.data.feed || [];
    } catch (error) {
      console.error('Error fetching stock news:', error);
      return [];
    }
  }
  
  public async handleQuery(query: string): Promise<string> {
    try {
      // Extract stock information from query
      const { symbols, timeframe, dataType } = await this.extractStocksInfo(query);
      
      if (symbols.length === 0) {
        return `I'm sorry, I couldn't identify any stock symbols in your query. Could you please specify which stocks you're interested in?`;
      }
      
      let stockData: any = {};
      
      // Get different types of data based on what was requested
      if (dataType === 'price' || dataType === 'current') {
        for (const symbol of symbols) {
          stockData[symbol] = {
            quote: await this.getStockPrice(symbol)
          };
        }
      } else if (dataType === 'trend' || dataType === 'history' || dataType === 'performance') {
        for (const symbol of symbols) {
          stockData[symbol] = {
            history: await this.getStockHistory(symbol, timeframe)
          };
        }
      } else if (dataType === 'news') {
        stockData.news = await this.getStockNews(symbols);
      } else {
        // Get a mix of data
        for (const symbol of symbols) {
          stockData[symbol] = {
            quote: await this.getStockPrice(symbol)
          };
        }
        stockData.news = await this.getStockNews(symbols);
      }
      
      const response = await callOpenAI(
        `You are a financial analyst providing stock market information. Create a helpful response to this query: "${query}"
        
        Use this REAL-TIME stock data to inform your response:
        ${JSON.stringify(stockData)}
        
        Include specific numbers and percentages when available.
        For price data, mention the current price and daily change.
        For historical data, summarize the trend over the requested time period.
        For news, highlight the most relevant recent developments.
        Add a disclaimer that this is not financial advice.
        Focus ONLY on answering the stock market question with the provided data.`
      );
      
      return response + "\n\nDisclaimer: This information is for educational purposes only and should not be considered financial advice. Always do your own research before making investment decisions.";
    } catch (error: any) {
      console.error('Error in stocks agent:', error);
      return `Sorry, I couldn't retrieve stock market information at this time. Error: ${error.message}`;
    }
  }
}