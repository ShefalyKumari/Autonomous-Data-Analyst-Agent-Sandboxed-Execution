import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("data/agent_memory.db")

class EpisodicMemoryManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_query TEXT NOT NULL,
                    generated_code TEXT,
                    analysis_summary TEXT,
                    chart_path TEXT,
                    execution_attempts INTEGER
                )
            """)
            conn.commit()

    def log_episode(self, session_id: str, query: str, code: str, summary: str, chart_path: str = "", attempts: int = 1):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_episodes (session_id, user_query, generated_code, analysis_summary, chart_path, execution_attempts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, query, code, summary, chart_path, attempts))
            conn.commit()

    def get_session_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_query, analysis_summary, chart_path, timestamp
                FROM conversation_episodes
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (session_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]