import streamlit as st

def render_chat_message(role: str, content: str):
    """Renders a chat message."""
    with st.chat_message(role):
        st.markdown(content)

def render_agent_step(step_type: str, content: str):
    """Renders an agent step (Plan, Code, Execution)."""
    with st.chat_message("assistant", avatar="🤖"):
        if step_type == "Plan":
            st.markdown(f"**📋 Execution Plan**")
            # If content is list, format it
            if isinstance(content, list):
                for i, step in enumerate(content, 1):
                    st.write(f"{i}. {step}")
            else:
                st.write(content)
                
        elif step_type == "Code":
            st.markdown(f"**💻 Generated Code**")
            st.code(content, language="bash")
            
        elif step_type == "Execution":
            st.markdown(f"**🚀 Execution Result**")
            if isinstance(content, dict):
                if content.get("return_code") == 0:
                    st.success("Success")
                    if content.get("stdout"):
                        with st.expander("Output"):
                            st.code(content["stdout"])
                else:
                    st.error(f"Failed (Code: {content.get('return_code')})")
                    st.code(content.get("stderr"), language="text")
            else:
                st.write(content)
