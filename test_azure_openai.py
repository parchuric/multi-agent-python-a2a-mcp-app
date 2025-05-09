import os
from dotenv import load_dotenv
from openai import AzureOpenAI

def test_azure_openai_api():
    """Test that the Azure OpenAI API credentials are valid and working."""
    load_dotenv()
    
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID")
    
    if not all([api_key, endpoint, deployment]):
        print("ERROR: Azure OpenAI credentials not found in environment variables!")
        print("Please check your .env file.")
        return False
    
    try:
        client = AzureOpenAI(
            api_key=api_key,  
            api_version="2023-09-15-preview",  # Use this or the most recent version that supports GPT-4.1
            azure_endpoint=endpoint
        )
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        print("Azure OpenAI API credentials are valid! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"Error testing Azure OpenAI API: {e}")
        return False

if __name__ == "__main__":
    test_azure_openai_api()