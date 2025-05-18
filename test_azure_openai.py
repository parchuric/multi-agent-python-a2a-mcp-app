import os
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
from pathlib import Path

def test_azure_openai_api():
    """Test that the Azure OpenAI API credentials are valid and working."""
    # Look for .env in the app directory
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / "app" / ".env"
    
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        # Try alternate location
        env_path = Path(os.path.dirname(os.path.abspath(__file__))) / ".env"
        if not env_path.exists():
            print(f"ERROR: .env file not found at {env_path} either")
            return False
    
    load_dotenv(dotenv_path=env_path)
    print(f"Loading environment from: {env_path}")
    
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID")
    version = os.environ.get("AZURE_OPENAI_API_VERSION")
    
    # Print the values for debugging (safely handle None values)
    if api_key:
        print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("API Key: Not found")
    
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {version}")
    
    if not all([api_key, endpoint, deployment]):
        print("ERROR: Azure OpenAI credentials not found in environment variables!")
        print("Please check your .env file.")
        return False
    
    try:
        # Use a hardcoded API version if the environment variable is empty
        if not version:
            version = "2024-05-01-preview"
            print(f"Using default API version: {version}")
        
        client = AzureOpenAI(
            api_key=api_key,  
            api_version=version,
            azure_endpoint=endpoint
        )
        
        # Standard API test first
        print("\n--- Testing Standard Chat Completions API ---")
        print(f"Creating completion with model: {deployment}")
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        print("Azure OpenAI API credentials are valid! Response:", response.choices[0].message.content)
        
        # Now test Responses API
        print("\n--- Testing Responses API Support ---")
        # Generate a unique conversation ID
        conversation_id = str(uuid.uuid4())
        print(f"Testing with conversation ID: {conversation_id}")
        
        try:
            print("Step 1: Creating first message with response_id=True...")
            first_response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "Remember this fact: The sky is blue."}],
                conversation_id=conversation_id,
                response_id=True
            )
            
            print(f"First response ID: {first_response.id}")
            print(f"First response content: {first_response.choices[0].message.content}")
            
            print("\nStep 2: Creating follow-up message with reference to first response...")
            follow_up = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "What fact did I ask you to remember?"}],
                conversation_id=conversation_id,
                references=[{"response_id": first_response.id}]
            )
            
            print(f"Follow-up response: {follow_up.choices[0].message.content}")
            print("\nSuccess! Azure OpenAI Responses API is working correctly.")
            
        except TypeError as e:
            if "unexpected keyword argument 'conversation_id'" in str(e):
                print("\nWarning: Your Azure OpenAI deployment doesn't support the Responses API.")
                print("This is likely because:")
                print("1. The API version doesn't support Responses API")
                print("2. Your Azure region doesn't have this feature enabled")
                print("3. Your model deployment doesn't support this feature")
                print("\nTry using api_version=2024-05-01-preview and check if your region supports it.")
            else:
                raise
        
        return True
    except Exception as e:
        print(f"Error testing Azure OpenAI API: {e}")
        return False

if __name__ == "__main__":
    test_azure_openai_api()