"""
Qiime Worker Agent
==================
Specialized agent for QIIME2 workflows.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from backend.utils.llm_client import get_llm
from backend.rag.retriever import get_retriever
from backend.agents.state import BioState

llm = get_llm()
retriever = get_retriever()

def qiime_worker(state: BioState) -> Dict[str, Any]:
    """
    Qiime Expert: Handles QIIME2 specific tasks.
    """
    print("📊 Qiime Worker: Processing...")
    
    current_step = state['current_step']
    file_structure = state.get('file_manifest', {}).get('raw_structure', "No file info.")
    errors = state.get('errors', [])
    
    # 1. Retrieve Context
    rag_docs = retriever.retrieve(f"QIIME2 {current_step}", k=2)
    rag_context = "\n\n".join(rag_docs)
    
    # 2. Generate Code with ULTRA-STRICT Prompt
    system_prompt = """You are a QIIME2 Command Generator. Output ONLY executable bash code.

CRITICAL RULES:
1. Output MUST start with #!/bin/bash or a direct command
2. NO explanations, NO analysis, NO markdown except code fences  
3. Use ONLY files from FILE STRUCTURE
4. Manifest format: sample-id\tabsolute-filepath\tdirection (TAB separated)
5. Sample IDs MUST be unique - use full filenames if needed

CONTEXT:
Environment: qiime2-amplicon-2024.2 (Conda)
Workspace: {workspace}

FILES ON SERVER:
{file_structure}

PREVIOUS ERROR (FIX IT):
{errors}

REFERENCE:
{context}

TASK: {task}

OUTPUT FORMAT (STRICT):
```bash
# Your executable code here
```
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Generate bash code for: {task}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "workspace": state.get('workspace_dir', '.'),
        "context": rag_context[:500],  # Limit context to avoid pollution
        "task": current_step,
        "file_structure": file_structure[:1000],  # Limit to avoid overflow
        "errors": errors[-1] if errors else "None"  # Only last error
    })
    
    code = response.content.strip()
    
    # Aggressive cleaning
    if "```bash" in code:
        code = code.split("```bash")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    # Remove any explanatory text that slipped through
    lines = code.split("\n")
    clean_lines = []
    for line in lines:
        # Skip lines that look like explanations
        if line.strip().startswith("**") or line.strip().startswith("Looking") or line.strip().startswith("Let me"):
            continue
        clean_lines.append(line)
    
    code = "\n".join(clean_lines)
        
    return {
        "next_agent": "executor",
        "generated_code": code
    }
