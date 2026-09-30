import os
import sys
import re
from typing import TypedDict, Optional
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from src.sandbox.executor import execute_sandboxed_code
from src.memory.memory_manager import EpisodicMemoryManager

DATA_PATH = "data/company_metrics.csv"
CHARTS_DIR = "outputs/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

class AgentState(TypedDict):
    session_id: str
    user_query: str
    code_snippet: str
    stdout: str
    stderr: str
    attempts: int
    max_attempts: int
    chart_path: str
    final_report: str
    status: str

# Local Llama 3.2 via Ollama
llm = OllamaLLM(model="llama3.2", temperature=0.1)
memory = EpisodicMemoryManager()

def extract_python_code(text: str) -> str:
    """Extract code block wrapped in ```python ... ``` or raw string."""
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

# --- Graph Nodes ---

def generate_code_node(state: AgentState) -> AgentState:
    """Writes or corrects analytical Python code based on tabular data."""
    query = state["user_query"]
    attempts = state["attempts"]
    last_err = state.get("stderr", "")

    if attempts == 0:
        prompt = f"""You are an expert Data Analyst & Python Engineer.
Target CSV file: '{DATA_PATH}'
Columns: customer_id, quarter, plan_tier, monthly_arr_usd, usage_hours, churn_flag, support_tickets, nps_score

Write clean, self-contained Python code to answer this question:
"{query}"

Guidelines:
1. Always import pandas as pd, matplotlib.pyplot as plt, and seaborn as sns.
2. Load data: df = pd.read_csv('{DATA_PATH}')
3. When grouping, always use `as_index=False` or `.reset_index()` (e.g., df.groupby('plan_tier', as_index=False)...) so grouped columns remain accessible.
4. Print key findings clearly using print() statements.
5. Save the primary visualization to '{CHARTS_DIR}/latest_chart.png' and call plt.close().
6. Output ONLY runnable Python code inside ```python ``` codeblocks. Do not include markdown commentary."""
    else:
        # Self-correction prompt incorporating the exact runtime error
        prompt = f"""Your previous Python script threw the following error:
---
{last_err}
---
Faulty Code:
{state['code_snippet']}

Fix the bug. Target CSV: '{DATA_PATH}'.
Columns: customer_id, quarter, plan_tier, monthly_arr_usd, usage_hours, churn_flag, support_tickets, nps_score
Note: If doing groupby, remember to use as_index=False or reset_index().
Output ONLY corrected, executable Python code in ```python ``` codeblocks."""

    raw_response = llm.invoke(prompt)
    code = extract_python_code(raw_response)

    state["code_snippet"] = code
    state["attempts"] += 1
    return state

def execute_sandbox_node(state: AgentState) -> AgentState:
    """Runs the code in the sandboxed subprocess and checks result."""
    result = execute_sandboxed_code(state["code_snippet"], timeout_seconds=12)

    state["stdout"] = result["stdout"]
    state["stderr"] = result["stderr"]

    chart_file = Path(f"{CHARTS_DIR}/latest_chart.png")
    if chart_file.exists():
        state["chart_path"] = str(chart_file)
    else:
        state["chart_path"] = ""

    return state

def synthesize_report_node(state: AgentState) -> AgentState:
    """Transforms raw stdout execution outputs into a structured executive report."""
    query = state["user_query"]
    stdout = state["stdout"]

    prompt = f"""You are a Lead Financial & Growth Intelligence Analyst.
User Question: "{query}"

Computed Execution Findings:
{stdout}

Write an executive-level analytical summary answering the user's question directly:
- State key metrics clearly (e.g. ARR, churn rates, ticket volume).
- Provide 2 concrete business takeaways.
- Keep the tone concise, authoritative, and data-backed."""

    report = llm.invoke(prompt)
    state["final_report"] = report.strip()
    state["status"] = "SUCCESS"

    # Persist episode into memory
    memory.log_episode(
        session_id=state["session_id"],
        query=query,
        code=state["code_snippet"],
        summary=state["final_report"],
        chart_path=state.get("chart_path", ""),
        attempts=state["attempts"]
    )
    return state

# --- Conditional Edge ---

def evaluate_execution_router(state: AgentState) -> str:
    """Routes to self-healing if error occurred and attempts < max_attempts."""
    if not state["stderr"] and state["stdout"]:
        return "synthesize"
    
    if state["attempts"] < state["max_attempts"]:
        print(f"-> Traceback detected. Triggering self-correction loop (Attempt {state['attempts']}/{state['max_attempts']})...")
        return "retry"
    
    return "synthesize"  # Fallback gracefully if max retries exhausted

# --- Build LangGraph Workflow ---

workflow = StateGraph(AgentState)

workflow.add_node("coder", generate_code_node)
workflow.add_node("sandbox", execute_sandbox_node)
workflow.add_node("reporter", synthesize_report_node)

workflow.set_entry_point("coder")
workflow.add_edge("coder", "sandbox")

workflow.add_conditional_edges(
    "sandbox",
    evaluate_execution_router,
    {
        "retry": "coder",
        "synthesize": "reporter"
    }
)
workflow.add_edge("reporter", END)

analyst_app = workflow.compile()