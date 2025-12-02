import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config import load_config

def render_sidebar():
    """Renders the sidebar with system status and config."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        config = load_config()
        
        # System Status
        st.subheader("System Status")
        st.success("🧠 Brain Node: Online (Windows)")
        st.success("💪 Muscle Node: Online (Ubuntu)")
        
        # Model Info
        st.subheader("🤖 Model Info")
        
        provider = config['llm']['active_provider']
        model_name = "Unknown"
        
        if provider == "online":
            import os
            from dotenv import load_dotenv
            load_dotenv()
            model_name = os.getenv("OPENAI_MODEL", "Unknown Online Model")
        elif provider == "local":
            model_name = config['llm']['providers']['local'].get('model', "Unknown Local Model")
            
        st.info(f"Model: {model_name}")
        st.caption(f"Provider: {provider}")
        
        # RAG Status
        st.subheader("📚 Knowledge Base")
        st.info(f"Collection: {config['rag']['collection_name']}")
        st.caption(f"Path: {config['rag']['persist_directory']}")
        
        st.divider()
        st.caption("v2.3 | Multi-Agent System")
