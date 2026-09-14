import sqlite3
from typing import Dict, Any, List, Optional
from .config import settings

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            kb_id TEXT PRIMARY KEY,
            base_url TEXT NOT NULL,
            status TEXT NOT NULL,
            pages_crawled INTEGER DEFAULT 0,
            chunks_created INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def upsert_kb(kb_id: str, base_url: str, status: str, pages_crawled: int = 0, chunks_created: int = 0, error: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO knowledge_bases (kb_id, base_url, status, pages_crawled, chunks_created, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(kb_id) DO UPDATE SET
        status = excluded.status,
        pages_crawled = excluded.pages_crawled,
        chunks_created = excluded.chunks_created,
        error_message = excluded.error_message
    """, (kb_id, base_url, status, pages_crawled, chunks_created, error))
    conn.commit()
    conn.close()

def get_kb(kb_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_bases WHERE kb_id = ?", (kb_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_kb_record(kb_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge_bases WHERE kb_id = ?", (kb_id,))
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()
