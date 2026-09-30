import os
import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.sandbox.executor import execute_sandboxed_code, validate_code_safety, SandboxSecurityError
from src.memory.memory_manager import EpisodicMemoryManager

client = TestClient(app)

def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_sandbox_clean_execution():
    code = "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2]})\nprint('SUM:', df['a'].sum())"
    res = execute_sandboxed_code(code)
    assert res["success"] is True
    assert "SUM: 3" in res["stdout"]

def test_sandbox_security_blocks_forbidden_imports():
    bad_code = "import os\nos.system('dir')"
    with pytest.raises(SandboxSecurityError):
        validate_code_safety(bad_code)

def test_sandbox_security_execution_result():
    bad_code = "import subprocess\nsubprocess.run(['ls'])"
    res = execute_sandboxed_code(bad_code)
    assert res["success"] is False
    assert "Security/Syntax Violation" in res["stderr"]

def test_episodic_memory_logging():
    mem = EpisodicMemoryManager()
    mem.log_episode(
        session_id="test-session-99",
        query="Test query?",
        code="print('hi')",
        summary="Test summary.",
        chart_path=""
    )
    history = mem.get_session_history("test-session-99")
    assert len(history) >= 1
    assert history[0]["user_query"] == "Test query?"