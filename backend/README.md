"""
README for Backend Implementation
"""

# Local-IA Backend (Brain Node)

## Components

### 1. main.py
FastAPI server that exposes the chat endpoint for the Streamlit frontend.

**Start the server:**
```bash
conda activate lab
cd e:\LabBio
python backend/main.py
```

### 2. ingest.py
Ingests lab protocol documents into ChromaDB vector database.

**Run ingestion:**
```bash
conda activate lab
cd e:\LabBio
python backend/ingest.py
```

### 3. agents.py
LangGraph-based multi-agent orchestration:
- **Planner Agent**: Breaks down tasks
- **Librarian Agent**: Retrieves protocols via RAG
- **Coder Agent**: Generates Bash scripts
- **Executor Agent**: Sends scripts to Ubuntu Muscle Node

### 4. config.yaml
Configuration file for paths, conda environments, and LLM settings.

## Dependencies
See `requirements.txt`. Install with:
```bash
pip install -r backend/requirements.txt
```

## Next Steps
1. Run `ingest.py` to populate the knowledge base
2. Start `main.py` to launch the Brain Node API
3. In another terminal, start the frontend: `streamlit run frontend/app.py`
