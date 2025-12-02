import streamlit as st
import sys
import time
from pathlib import Path

# Add project root to sys.path
# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_chat_message, render_agent_step
from backend.agents.graph import create_graph
from langchain_core.messages import HumanMessage

# Page Config
st.set_page_config(
    page_title="Local-IA BioAssistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better progress display
st.markdown("""
<style>
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    .step-indicator {
        font-size: 0.9em;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render Sidebar (Simplified)
render_sidebar()

# Main Layout
st.title("🧬 Local-IA Intelligent Assistant")

# Create Tabs
tab_chat, tab_terminal = st.tabs(["💬 Chat Interface", "🖥️ Terminal Monitor"])

# --- Chat Tab ---
with tab_chat:
    st.caption("Powered by Multi-Agent System (Supervisor + Workers) | Windows Brain + Ubuntu Muscle")
    
    # Render Chat History
    for msg in st.session_state.messages:
        if msg["type"] == "user":
            render_chat_message("user", msg["content"])
        elif msg["type"] == "assistant":
            render_chat_message("assistant", msg["content"])
        elif msg["type"] == "step":
            render_agent_step(msg["step_type"], msg["content"])

    # User Input
    if prompt := st.chat_input("How can I help you with your analysis?"):
        # Add user message to state
        st.session_state.messages.append({"type": "user", "content": prompt})
        render_chat_message("user", prompt)
        
        # Run Agent
        with st.spinner("Thinking..."):
            try:
                app = create_graph()
                initial_state = {
                    "messages": [HumanMessage(content=prompt)],
                    "plan": [],
                    "current_step": "",
                    "file_manifest": {},
                    "qc_metrics": {},
                    "errors": []
                }
                
                # Create progress containers
                status_container = st.empty()
                progress_container = st.container()
                
                # Stream events
                current_step_display = ""
                step_count = 0
                total_steps = 0
                
                for output in app.stream(initial_state, {"recursion_limit": 50}):
                    for node_name, node_state in output.items():
                        step_count += 1
                        
                        # Update current status with emoji
                        if node_name == "supervisor":
                            current_step_display = "🧠 **Supervisor**: Analyzing and Planning"
                            if "plan" in node_state:
                                total_steps = len(node_state["plan"])
                        elif node_name == "obitools":
                            current_step_display = "🦠 **OBITools Agent**: Generating Code"
                        elif node_name == "qiime":
                            current_step_display = "📊 **QIIME2 Agent**: Generating Code"
                        elif node_name == "executor":
                            current_step_display = "🚀 **Executor**: Running on Ubuntu Server"
                        
                        # Display status
                        status_html = f'<div class="status-box">{current_step_display}</div>'
                        if total_steps > 0:
                            status_html += f'<div class="step-indicator">Progress: Step {step_count}/{total_steps*2}</div>'
                        status_container.markdown(status_html, unsafe_allow_html=True)
                        
                        # Handle Supervisor Output
                        if node_name == "supervisor":
                            if "plan" in node_state:
                                plan = node_state["plan"]
                                with progress_container:
                                    st.success(f"📋 **Plan Generated**: {len(plan)} steps")
                                    with st.expander("View Full Plan"):
                                        for i, step in enumerate(plan, 1):
                                            st.write(f"{i}. {step}")
                                st.session_state.messages.append({"type": "step", "step_type": "Plan", "content": plan})
                        
                        # Handle Workers Output (Obitools/Qiime)
                        elif node_name in ["obitools", "qiime"]:
                            if "generated_code" in node_state:
                                code = node_state["generated_code"]
                                with progress_container:
                                    st.info(f"💻 **Code Generated by {node_name.upper()}**")
                                    st.code(code, language="bash")
                                st.session_state.messages.append({"type": "step", "step_type": "Code", "content": code})
                        
                        # Handle Executor Output
                        elif node_name == "executor":
                            if "last_execution_result" in node_state:
                                result = node_state["last_execution_result"]
                                with progress_container:
                                    if result["return_code"] == 0:
                                        st.success("✅ **Execution Successful**")
                                        if result["stdout"]:
                                            with st.expander("View Output"):
                                                st.text(result["stdout"])
                                    else:
                                        st.error("❌ **Execution Failed**")
                                        st.code(result["stderr"], language="text")
                                st.session_state.messages.append({"type": "step", "step_type": "Execution", "content": result})
                
                # Clear status
                status_container.empty()
                
                # Final Success Message
                final_msg = "✅ Task Completed Successfully!"
                st.session_state.messages.append({"type": "assistant", "content": final_msg})
                with progress_container:
                    st.balloons()
                    st.success(final_msg)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                import traceback
                st.code(traceback.format_exc())

# --- Terminal Tab ---
with tab_terminal:
    st.markdown("### 🚀 Real-time Ubuntu Terminal Log")
    log_path = Path(__file__).parent.parent / "Documents" / "logs" / "executor.log"
    
    log_placeholder = st.empty()
    
    # Read log
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Show last 100 lines
            log_content = "".join(lines[-100:])
        log_placeholder.code(log_content, language="text")
    else:
        log_placeholder.info("No logs found yet.")
        
    if st.button("Refresh Terminal"):
        st.rerun()
