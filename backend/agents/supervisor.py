"""
Supervisor Agent
================
The Brain of the Multi-Agent System.
Parses intent, scans directory, plans tasks, and routes to workers.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from backend.utils.llm_client import get_llm
from backend.agents.state import BioState
from backend.utils.executor_client import ExecutorClient

llm = get_llm()
executor_client = ExecutorClient()

def extract_path_with_llm(user_request: str) -> str:
    """
    Uses LLM to extract the absolute path from the user request.
    Handles mixed text/path scenarios.
    """
    system_prompt = """You are a Path Extractor.
    Your ONLY job is to identify the absolute file path in the user's request.
    
    Rules:
    1. Extract the full absolute path (e.g., /media/dell/...).
    2. Ignore any surrounding text (e.g., "process data in", "contains files").
    3. If multiple paths exist, return the most likely 'root' directory.
    4. Return ONLY the path string. No markdown, no quotes.
    5. If no path is found, return "None".
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{request}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"request": user_request})
    return response.content.strip()

def supervisor_node(state: BioState) -> Dict[str, Any]:
    """
    Supervisor: Plans and Routes.
    """
    print("🧠 Supervisor: Thinking...")
    
    messages = state['messages']
    user_request = messages[-1].content
    
    # If we already have a plan and are executing, check status
    if state.get('plan') and state.get('current_step'):
        # Re-entry logic
        plan = state['plan']
        current_step_str = state['current_step']
        
        # Check for errors from previous step
        errors = state.get('errors', [])
        if errors:
            print(f"⚠️ Error Detected: {errors[-1]}")
            
            # Check Retry Count
            retry_count = state.get('retry_count', 0)
            if retry_count >= 3:
                print("❌ Max Retries Reached. Aborting.")
                return {"final_answer": f"Task Failed after 3 retries. Last Error: {errors[-1]}"}
            
            # If error, route back to the SAME agent to retry
            # We need to know who executed the last step.
            # For now, let's infer from the plan step text
            last_agent = "obitools"
            if "qiime" in current_step_str.lower():
                last_agent = "qiime"
            
            print(f"🔄 Routing back to {last_agent} for correction (Attempt {retry_count + 1})...")
            return {
                "next_agent": last_agent,
                "retry_count": retry_count + 1
                # We don't advance the step, we retry
            }

        try:
            current_idx = plan.index(current_step_str)
            if current_idx + 1 < len(plan):
                next_step = plan[current_idx + 1]
                
                # Decide agent for next step
                next_agent = "obitools"
                if "qiime" in next_step.lower() or "dada2" in next_step.lower() or "diversity" in next_step.lower():
                    next_agent = "qiime"
                    
                print(f"👉 Next Step: {next_step} -> {next_agent}")
                return {
                    "current_step": next_step,
                    "next_agent": next_agent,
                    "errors": [], # Clear errors on success
                    "retry_count": 0 # Reset retry count
                }
            else:
                return {"final_answer": "All steps completed successfully."}
                
        except ValueError:
            return {"error": "Plan synchronization error."}

    else:
        # --- Initial Planning Phase ---
        
        # 1. Directory Analysis (Pre-planning)
        # Use LLM to extract path
        target_dir = extract_path_with_llm(user_request)
        print(f"🔍 Extracted Target Directory: {target_dir}")
        
        file_structure = "No directory specified or found."
        
        if target_dir and target_dir != "None":
            # Run ls -R via Executor
            # We use a simple ls -R to get file list
            # Quote the path to handle spaces
            cmd_result = executor_client.run_command(f"ls -R '{target_dir}'")
            if cmd_result['return_code'] == 0:
                file_structure = cmd_result['stdout']
                # Limit output size to avoid context overflow
                if len(file_structure) > 2000:
                    file_structure = file_structure[:2000] + "\n...(truncated)..."
            else:
                file_structure = f"Error scanning directory: {cmd_result['stderr']}"
        
        print(f"📂 File Structure:\n{file_structure[:200]}...")

        # 2. Generate Plan
        system_prompt = """You are the Supervisor of a Bioinformatics Agent Team.
        
        Your Goal:
        1. Analyze the user request and the provided FILE STRUCTURE.
        2. Create a high-level execution plan.
        3. For the FIRST step, decide which worker to assign.
        
        FILE STRUCTURE (Real files on server):
        {file_structure}
        
        CRITICAL RULES:
        1. Use ONLY filenames that actually exist in the File Structure.
        2. Do NOT hallucinate files like 'sample1.fastq' if they are not there.
        3. Always start with a 'Create Workspace' step.
        
        Workers:
        - 'obitools': For sequence merging, filtering, OBITools3 commands.
        - 'qiime': For denoising, taxonomy, diversity analysis, QIIME2 commands.
        
        Output Format (JSON):
        {{
            "plan": ["1. Create workspace...", "2. Import data...", ...],
            "current_step": "1. Create workspace...",
            "next_agent": "obitools"
        }}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{request}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "request": user_request,
            "file_structure": file_structure
        })
        
        try:
            # Parse JSON output
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
            elif content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
                
            result = json.loads(content)
            
            print(f"📋 Plan: {len(result['plan'])} steps")
            print(f"👉 Routing to: {result['next_agent']}")
            
            return {
                "plan": result['plan'],
                "current_step": result['current_step'],
                "next_agent": result['next_agent'],
                # Store file manifest for workers to use
                "file_manifest": {"raw_structure": file_structure} 
            }
            
        except Exception as e:
            print(f"❌ Supervisor Error: {e}")
            return {"error": str(e)}
