"""
Obitools Worker Agent
=====================
Specialized agent for OBITools3 workflows.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from backend.utils.llm_client import get_llm
from backend.rag.retriever import get_retriever
from backend.agents.state import BioState

llm = get_llm()
retriever = get_retriever()

def obitools_worker(state: BioState) -> Dict[str, Any]:
    """
    Obitools Expert: Handles OBITools3 specific tasks.
    """
    print("🦠 Obitools Worker: Processing...")
    
    current_step = state['current_step']
    file_structure = state.get('file_manifest', {}).get('raw_structure', "No file info.")
    errors = state.get('errors', [])
    
    # 1. Retrieve Context
    rag_docs = retriever.retrieve(f"OBITools {current_step}", k=3)
    rag_context = "\n\n".join(rag_docs)
    
    # 2. Generate Code
    system_prompt = """You are an Expert OBITools3 Bioinformatician.
    Your goal is to generate Python or Shell commands for OBITools3 processing.
    
    EXECUTION CONTEXT:
    - Running on Ubuntu Linux.
    - Environment: 'obi3' (Conda).
    - Workspace: {workspace}
    
    FILE STRUCTURE (Real files):
    {file_structure}
    
    PREVIOUS ERRORS (Fix these if present):
    {errors}
    
    CAPABILITIES:
    1. Map File Parsing: If asked to parse a map file, write Python code to read the file and extract sample names/barcodes.
    2. Batch Processing: Use loops for multiple samples (JC1..JCn).
    3. Dynamic Thresholds: Use 'obi grep' with thresholds found in RAG context.
    
    CRITICAL RULES:
    1. Use ONLY filenames that appear in FILE STRUCTURE.
    2. Do NOT hallucinate files.
    3. If a file is missing, print an error message in the script.
    
    RAG CONTEXT:
    {context}
    
    OUTPUT:
    Return ONLY the executable code block.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Current Task: {task}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "workspace": state.get('workspace_dir', '.'),
        "context": rag_context,
        "task": current_step,
        "file_structure": file_structure,
        "errors": "\n".join(errors) if errors else "None"
    })
    
    code = response.content.strip()
    # Clean markdown
    if code.startswith("```"):
        code = code.split("\n", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("\n", 1)[0]
        
    return {
        "next_agent": "executor",
        "generated_code": code
    }
