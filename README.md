# Autonomous Financial & Data Analyst Agent with Sandboxed Code Execution & Episodic Memory

An enterprise-grade autonomous analytical agent built using LangGraph, Python sandboxing, and local LLM execution. The system parses business intelligence queries, synthesizes data analysis code, executes it in an isolated security sandbox, dynamically self-heals runtime errors via traceback reflection loops, and persists multi-turn session history in SQLite.

---

## Architecture Flow

```text
               +----------------------------------------------------+
               |                User Natural Query                  |
               |      ("Analyze Q3 churn & plot ARR trajectory")     |
               +-------------------------+--------------------------+
                                         |
                                         v
+-------------------------------------------------------------------+
|               Agent Orchestration Loop (LangGraph)                |
|                                                                   |
|   +-------------------+        +------------------------------+   |
|   | Episodic Memory   |<------>| Intent Parser & Task Planner |   |
|   | (SQLite / Schema) |        +--------------+---------------+   |
|   +-------------------+                       |                   |
|                                               v                   |
|                                +------------------------------+   |
|                                | Code Synthesis Node (Python) |   |
|                                +--------------+---------------+   |
|                                               |                   |
|                   +---------------------------+                   |
|                   |                           |                   |
|                   v                           v                   |
|   +-------------------------------+   +-----------------------+   |
|   | Runtime Traceback Interceptor |   |  Sandboxed Execution  |   |
|   | (Self-Correction Loop: max 3x)|<--|  (Isolated Subprocess)|   |
|   +---------------+---------------+   +-----------+-----------+   |
|                   ^                               | (Success)     |
|                   +--- (Error / Non-Zero Exit) ---+               |
|                                                   |               |
|                                                   v               |
|                                       +-----------------------+   |
|                                       | Report & Visualization|   |
|                                       | Synthesizer (Markdown)|   |
|                                       +-----------------------+   |
+---------------------------------------------------+---------------+
                                                    |
                                                    v
                    +-----------------------------------------------+
                    |             Serving & Interfaces              |
                    |   * Streamlit Interactive Analyst Workspace   |
                    |   * FastAPI Execution REST API                |
                    |   * Automated pytest Validation Suite         |
                    +-----------------------------------------------+