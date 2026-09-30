from src.agent.analyst_graph import analyst_app

initial_state = {
    "session_id": "session-test-01",
    "user_query": "What is the average monthly ARR and churn rate broken down by plan_tier?",
    "code_snippet": "",
    "stdout": "",
    "stderr": "",
    "attempts": 0,
    "max_attempts": 3,
    "chart_path": "",
    "final_report": "",
    "status": "INITIALIZED"
}

print("Executing Autonomous Analyst Agent...")
final_output = analyst_app.invoke(initial_state)

print("\n" + "=" * 60)
print("EXECUTED CODE SNIPPET:")
print("=" * 60)
print(final_output["code_snippet"])

print("\n" + "=" * 60)
print("SANDBOX STDOUT OUTPUT:")
print("=" * 60)
print(final_output["stdout"])

print("\n" + "=" * 60)
print("EXECUTIVE SUMMARY REPORT:")
print("=" * 60)
print(final_output["final_report"])