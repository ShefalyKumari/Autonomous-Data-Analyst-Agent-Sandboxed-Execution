import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agent.analyst_graph import analyst_app
from src.memory.memory_manager import EpisodicMemoryManager

st.set_page_config(
    page_title="Autonomous Financial Analyst Agent",
    page_icon="📈",
    layout="wide"
)

memory = EpisodicMemoryManager()

st.title("📈 Autonomous Financial & Data Analyst Agent")
st.caption("Self-Healing Code Execution, Persistent SQLite Memory & Automated Visualizations")

# Sidebar
with st.sidebar:
    st.header("Agent Control Center")
    session_id = st.text_input("Active Session ID:", value="session-prod-01")
    
    st.subheader("Target Dataset Preview")
    csv_path = "data/company_metrics.csv"
    if os.path.exists(csv_path):
        preview_df = pd.read_csv(csv_path)
        st.dataframe(preview_df.head(5), height=180)
        st.caption(f"Total Rows: {len(preview_df)} | Total Columns: {len(preview_df.columns)}")

    st.divider()
    st.subheader("Episodic Memory Feed")
    history = memory.get_session_history(session_id, limit=3)
    for h in history:
        with st.expander(f"Q: {h['user_query'][:35]}..."):
            st.caption(f"Time: {h['timestamp']}")
            st.write(h['analysis_summary'][:150] + "...")

# Main Layout
col_query, col_out = st.columns([1, 1])

with col_query:
    st.subheader("Business Intelligence Query")
    sample_queries = [
        "What is the average monthly ARR and churn rate broken down by plan_tier?",
        "Which quarter had the highest total revenue and how does it correlate with usage hours?",
        "Compare the average NPS score between churned and non-churned customers."
    ]
    selected_sample = st.selectbox("Select a benchmark prompt (or write your own below):", sample_queries)
    user_query = st.text_area("Your Analytical Request:", value=selected_sample, height=90)
    run_btn = st.button("Execute Autonomous Analysis", type="primary")

with col_out:
    st.subheader("Executive Intelligence Report")
    if run_btn and user_query.strip():
        with st.spinner("Agent generating code, running in sandbox, and evaluating outputs..."):
            state = {
                "session_id": session_id,
                "user_query": user_query,
                "code_snippet": "",
                "stdout": "",
                "stderr": "",
                "attempts": 0,
                "max_attempts": 3,
                "chart_path": "",
                "final_report": "",
                "status": "INITIALIZED"
            }
            output = analyst_app.invoke(state)

            st.markdown(output["final_report"])

            if output.get("chart_path") and os.path.exists(output["chart_path"]):
                st.image(output["chart_path"], caption="Generated Analytics Chart", use_container_width=True)

            with st.expander("🛠️ View Agent Inspection & Code Sandbox Telemetry"):
                st.write(f"**Execution Attempts:** {output['attempts']}")
                st.code(output["code_snippet"], language="python")
                st.write("**Sandbox Output (stdout):**")
                st.text(output["stdout"] if output["stdout"] else "No stdout.")
                if output["stderr"]:
                    st.write("**Sandbox Errors (stderr):**")
                    st.error(output["stderr"])