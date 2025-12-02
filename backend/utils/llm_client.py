"""
LLM Client Module
=================
Provides a unified interface for Local and Online LLMs.
Loads configuration from .env and config.yaml.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sys
# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config import load_config

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

def get_llm():
    """
    Get the configured LLM client.
    Returns:
        ChatOpenAI: Configured LangChain chat model
    """
    config = load_config()
    provider_type = config['llm']['active_provider']
    
    if provider_type == 'online':
        # Load from Environment Variables (Standard OpenAI SDK format)
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model_name = os.getenv("OPENAI_MODEL")
        
        if not api_key or "your_api_key_here" in api_key:
            raise ValueError("❌ Please set OPENAI_API_KEY in e:\\LabBio\\.env")
            
        print(f"🤖 Initializing Online LLM: {model_name}")
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.1
        )
        
    elif provider_type == 'local':
        # Load from config.yaml
        local_config = config['llm']['providers']['local']
        print(f"🤖 Initializing Local LLM: {local_config['model']}")
        return ChatOpenAI(
            model=local_config['model'],
            openai_api_key=local_config['api_key'],
            openai_api_base=local_config['api_base'],
            temperature=0.1
        )
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

if __name__ == "__main__":
    # Test the client
    try:
        llm = get_llm()
        print("\n💬 Testing connection...")
        response = llm.invoke("Hello! Who are you?")
        print(f"✅ Response: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
