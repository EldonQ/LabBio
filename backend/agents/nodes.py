"""
Shared Agent Nodes
==================
Contains shared nodes like the Executor.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.utils.executor_client import ExecutorClient
from backend.agents.state import BioState

# Initialize clients
executor_client = ExecutorClient()

def executor_node(state: BioState) -> Dict[str, Any]:
    """
    Executor Node: Executes the generated code on the local executor service.
    """
    # In the new architecture, code comes from 'generated_code' key passed by workers
    # But wait, BioState doesn't have 'generated_code' field in the definition I wrote earlier?
    # Let's check BioState definition.
    # I didn't add 'generated_code' to BioState.
    # Workers return {"generated_code": code} which gets merged into state?
    # No, TypedDict doesn't allow extra fields unless total=False.
    
    # I need to add 'generated_code' to BioState or pass it differently.
    # Let's assume I add it to BioState.
    
    code = state.get('generated_code')
    workspace_dir = state.get('workspace_dir')
    
    if not code:
        print("⚠️ Executor: No code to execute.")
        return {"error": "No code generated."}

    print("🚀 Executor: Running code...")
    
    # Determine environment based on code content (simple heuristic)
    env_name = "base"
    if "obi" in code or "OBITools" in code:
        env_name = "obi3"
    elif "qiime" in code:
        env_name = "qiime2-amplicon-2024.2"
        
    # Execute
    # Heuristic: If code contains "mkdir", we try to extract the path to update state
    new_workspace = None
    if "mkdir" in code:
        import re
        # Look for path after mkdir -p or mkdir
        match = re.search(r'mkdir\s+(?:-p\s+)?([^\s]+)', code)
        if match:
            new_workspace = match.group(1)
            print(f"  📂 Detected Workspace Creation: {new_workspace}")
    
    # If we already have a workspace, use it as CWD. 
    cwd = workspace_dir
    if new_workspace:
        cwd = None # Run in default/parent for creation
        
    result = executor_client.run_command(script=code, cwd=cwd, env_name=env_name)
    
    print(f"  ⚙️ Return Code: {result['return_code']}")
    
    updates = {}
    if result['return_code'] != 0:
        print(f"  ❌ Error: {result['stderr'][:200]}...")
        updates["errors"] = state.get("errors", []) + [result['stderr']]
    else:
        print(f"  ✅ Success")
        updates["errors"] = [] # Explicitly clear errors on success
        if new_workspace:
            updates["workspace_dir"] = new_workspace
            
    # Clear generated code after execution
    updates["generated_code"] = None
    updates["last_execution_result"] = result
    
    return updates
