import express from 'express';
import bodyParser from 'body-parser';
import path from 'path';
import dotenv from 'dotenv';
// Import the new LangGraph processor
import { processQuery } from './graph/langGraph';

// Load environment variables
dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '..', 'public')));

// API endpoint to handle queries
app.post('/api/query', async (req, res) => {
  try {
    const { query } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }
    
    // Use LangGraph to process the query
    const response = await processQuery(query);
    
    // Extract topic from response for UI display
    // In a real implementation, you might want to include topic in the returned state
    const topicRegex = /(weather|sports|news|stocks|health)/i;
    const topicMatch = response.match(topicRegex);
    const topic = topicMatch ? topicMatch[0].toLowerCase() : 'general';
    
    res.json({ 
      response, 
      topic,
    });
  } catch (error: any) {
    console.error('Error processing query:', error);
    res.status(500).json({ 
      error: 'Failed to process your request', 
      message: error instanceof Error ? error.message : String(error) 
    });
  }
});

// Serve the main HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});