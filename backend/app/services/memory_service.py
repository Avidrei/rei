import sqlite3
import os
import json
from typing import List, Dict, Any
from app.config import settings

DB_PATH = os.path.join(settings.BASE_DIR, "app", "storage", "history.db")

class AssistantMemory:
    def __init__(self) -> None:
        # Connect to a local, free, lightweight SQLite file store
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._initialize_db()

    def _initialize_db(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    routing_track TEXT NULL
                )
            """)

    def append_message(self, sender: str, message: str, track: str | None = None) -> None:
        """Saves a conversational turn securely into local disk storage."""
        with self.conn:
            self.conn.execute(
                "INSERT INTO chat_logs (sender, message, routing_track) VALUES (?, ?, ?)",
                (sender, message, track)
            )

    def fetch_recent_context(self, limit: int = 6) -> List[Dict[str, str]]:
        """Retrieves the recent history loop formatted for LLM consumption."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT sender, message FROM chat_logs ORDER BY id DESC LIMIT ?", 
            (limit,)
        )
        rows = cursor.fetchall()
        # History needs to be read in chronological order, so reverse the fetched list
        rows.reverse()
        return [{"role": "user" if r[0] == "user" else "model", "parts": [r[1]]} for r in rows]

    def clear_all_memory(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM chat_logs")

# Register singleton instance
memory_service = AssistantMemory()