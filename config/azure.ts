export const config = {
  endpoint: process.env.AZURE_OPENAI_ENDPOINT || '',
  apiKey: process.env.AZURE_OPENAI_API_KEY || '',
  deploymentId: process.env.AZURE_OPENAI_DEPLOYMENT_ID || 'gpt-4-1',
};