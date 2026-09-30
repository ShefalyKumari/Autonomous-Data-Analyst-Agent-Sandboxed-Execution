import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agent.analyst_graph import analyst_app
from src.memory.memory_manager import EpisodicMemoryManager

app = FastAPI(
    title="Autonomous Financial & Data Analyst Agent API",
    description="Agentic code execution, self-correction, and persistent memory service",
    version="1.0.0"
)

memory = EpisodicMemoryManager()

class QueryRequest(BaseModel):
    session_id: str = Field(default="session-web-01", json_schema_extra={"example": "session-web-01"})
    query: str = Field(..., json_schema_extra={"example": "Which plan tier has the highest average monthly ARR?"})

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Autonomous-Analyst-Agent"}

@app.post("/analyze")
def analyze(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    initial_state = {
        "session_id": req.session_id,
        "user_query": req.query,
        "code_snippet": "",
        "stdout": "",
        "stderr": "",
        "attempts": 0,
        "max_attempts": 3,
        "chart_path": "",
        "final_report": "",
        "status": "INITIALIZED"
    }

    result = analyst_app.invoke(initial_state)

    return {
        "session_id": req.session_id,
        "query": req.query,
        "code_executed": result["code_snippet"],
        "stdout": result["stdout"],
        "error": result["stderr"],
        "chart_generated": bool(result.get("chart_path")),
        "executive_report": result["final_report"],
        "total_attempts": result["attempts"]
    }

@app.get("/history/{session_id}")
def get_history(session_id: str):
    history = memory.get_session_history(session_id)
    return {"session_id": session_id, "history": history}