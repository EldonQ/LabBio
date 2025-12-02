"""
Multi-Agent Graph Definition
============================
Connects Supervisor, Workers, and Executor.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from backend.agents.state import BioState
from backend.agents.supervisor import supervisor_node
from backend.agents.workers.obitools import obitools_worker
from backend.agents.workers.qiime import qiime_worker
from backend.agents.nodes import executor_node # Reuse existing executor node

def router(state: BioState):
    """Route to the next agent based on Supervisor's decision"""
    if state.get('final_answer'):
        return END
    if state.get('error'):
        return END
    return state['next_agent']

def worker_router(state: BioState):
    """Workers always send code to Executor"""
    return "executor"

def executor_router(state: BioState):
    """Executor always goes back to Supervisor to update plan"""
    if state.get('error'):
        return END
    return "supervisor"

def create_graph():
    """Create the Multi-Agent workflow graph"""
    workflow = StateGraph(BioState)
    
    # Add Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("obitools", obitools_worker)
    workflow.add_node("qiime", qiime_worker)
    workflow.add_node("executor", executor_node)
    
    # Define Edges
    workflow.set_entry_point("supervisor")
    
    # Supervisor -> Workers
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "obitools": "obitools",
            "qiime": "qiime",
            END: END
        }
    )
    
    # Workers -> Executor
    workflow.add_edge("obitools", "executor")
    workflow.add_edge("qiime", "executor")
    
    # Executor -> Supervisor (Loop back for next step)
    workflow.add_edge("executor", "supervisor")
    
    return workflow.compile()

if __name__ == "__main__":
    # Test the graph
    from langchain_core.messages import HumanMessage
    print("🚀 Starting Multi-Agent Graph Test...")
    app = create_graph()
    
    initial_state = {
        "messages": [HumanMessage(content="Create a workspace named 'test_multiagent' and check OBITools version")],
        "plan": [],
        "current_step": "",
        "file_manifest": {},
        "qc_metrics": {},
        "errors": []
    }
    
    for output in app.stream(initial_state, {"recursion_limit": 50}):
        for key, value in output.items():
            print(f"Finished Node: {key}")
