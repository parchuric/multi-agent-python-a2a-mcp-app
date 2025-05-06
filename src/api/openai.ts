import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
const apiKey = process.env.AZURE_OPENAI_API_KEY;
const deploymentId = process.env.AZURE_OPENAI_DEPLOYMENT_ID;

export async function callOpenAI(prompt: string): Promise<string> {
  try {
    if (!endpoint || !apiKey || !deploymentId) {
      throw new Error('Azure OpenAI configuration is incomplete. Check your environment variables.');
    }

    const response = await axios.post(
      `${endpoint}/openai/deployments/${deploymentId}/chat/completions?api-version=2023-07-01-preview`,
      {
        messages: [
          { role: "system", content: "You are a helpful assistant." },
          { role: "user", content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 800
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'api-key': apiKey
        }
      }
    );

    return response.data.choices[0].message.content;
  } catch (error) {
    console.error('Error calling Azure OpenAI:', 
      axios.isAxiosError(error) ? error.response?.data || error.message : error);
    throw new Error('Failed to get response from language model');
  }
}