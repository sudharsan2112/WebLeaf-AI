from typing import List, Dict
from .database import get_connection

class ChatMemory:
    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)", 
                       (self.session_id, role, content))
        conn.commit()
        
        # Enforce max history limit (*2 for user + assistant pairs)
        cursor.execute("""
            DELETE FROM chat_history 
            WHERE session_id = ? AND id NOT IN (
                SELECT id FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
            )
        """, (self.session_id, self.session_id, self.max_history * 2))
        conn.commit()
        conn.close()

    def get_history(self) -> List[Dict[str, str]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC", (self.session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
