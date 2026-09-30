import sys
import subprocess
import tempfile
import ast
from pathlib import Path
from typing import Dict, Any

# Dangerous AST function calls or imports to reject
FORBIDDEN_CALLS = {"system", "popen", "spawn", "rmtree", "unlink", "kill"}
FORBIDDEN_MODULES = {"subprocess", "shutil", "socket", "http", "requests"}

class SandboxSecurityError(Exception):
    """Raised when generated code violates execution safety constraints."""
    pass

def validate_code_safety(code: str) -> None:
    """Parses Python AST to ensure code doesn't execute malicious system calls."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Generated code failed syntax parse: {str(e)}")

    for node in ast.walk(tree):
        # Disallow prohibited imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    raise SandboxSecurityError(f"Import of forbidden module '{alias.name}' detected.")
        elif isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_MODULES:
                raise SandboxSecurityError(f"Import from forbidden module '{node.module}' detected.")

        # Disallow dangerous attribute calls like os.system
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in FORBIDDEN_CALLS:
                    raise SandboxSecurityError(f"Execution of dangerous method '{node.func.attr}' blocked.")

def execute_sandboxed_code(code: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    """
    Executes Python script in an isolated subprocess, capturing outputs, charts, or errors.
    """
    try:
        validate_code_safety(code)
    except (SandboxSecurityError, SyntaxError) as err:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Security/Syntax Violation: {str(err)}",
            "returncode": 1
        }

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_script:
        temp_script.write(code)
        temp_path = temp_script.name

    try:
        process = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        return {
            "success": process.returncode == 0,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"TimeoutError: Script execution exceeded {timeout_seconds}s limit.",
            "returncode": -1
        }
    finally:
        # Clean up temporary execution script
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass