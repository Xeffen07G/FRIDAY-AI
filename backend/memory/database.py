import shutil
import os
import sqlite3
import uuid
from datetime import datetime
from backend.core.logger import get_logger

logger = get_logger("memory.database")

DB_PATH = "friday_memory.db"
BACKUP_PATH = "friday_memory.db.bak"

def backup_database():
    """Creates a backup snapshot of the database."""
    if os.path.exists(DB_PATH):
        try:
            shutil.copy2(DB_PATH, BACKUP_PATH)
            logger.info("Database backup created successfully.")
        except Exception as e:
            logger.error(f"Database backup failed: {e}")

def get_connection():
    """Returns a new SQLite connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at DATETIME,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_session(title="New Chat"):
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now)
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "title": title}

def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def update_session_title(session_id: str, new_title: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (new_title, datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()

import logging
logger = logging.getLogger("friday.memory.database")

def save_message(session_id: str, role: str, content: str):
    try:
        logger.info(f"Attempting to save {role} message to session {session_id} (len: {len(content)})")
        msg_id = str(uuid.uuid4())
        # Use string format for datetime to ensure SQLite compatibility without adapters
        now = datetime.now().isoformat()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, session_id, role, content, now)
        )
        logger.info(f"Insert query executed for message {msg_id}")
        
        cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully committed message {msg_id} to DB.")
        return msg_id
        
    except Exception as e:
        logger.error(f"FATAL DB ERROR in save_message: {str(e)}", exc_info=True)
        raise

def get_messages(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    messages = [{"id": row["id"], "sender": row["role"], "text": row["content"], "created_at": row["created_at"]} for row in cursor.fetchall()]
    conn.close()
    return messages

def delete_session(session_id: str):
    conn = get_connection()
    conn.cursor().execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.cursor().execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def session_exists(session_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Initialize DB on import
init_db()
