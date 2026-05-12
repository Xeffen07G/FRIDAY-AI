import sqlite3
import os
import uuid
import time
from datetime import datetime
from core.logger import get_logger

logger = get_logger("memory.database")

DB_PATH = "friday_memory.db"
BACKUP_PATH = "friday_memory.db.bak"

def backup_database():
    """Creates a safe hot backup snapshot of the database using SQLite's backup API."""
    if not os.path.exists(DB_PATH):
        return
    try:
        # Use hot backup API to prevent WinError 32 locking issues
        src = sqlite3.connect(DB_PATH, timeout=10)
        dst = sqlite3.connect(BACKUP_PATH, timeout=10)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        logger.info("Database hot backup created successfully.")
    except Exception as e:
        logger.error(f"Database hot backup failed: {e}")

def get_connection():
    """Returns a new SQLite connection with WAL mode and timeout resilience."""
    # check_same_thread=False allows sharing connection between threads (safe for our usage)
    # timeout=20 ensures we wait for locks to release before failing
    conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable Write-Ahead Logging (WAL) for true concurrency
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except sqlite3.Error as e:
        logger.warning(f"Failed to set PRAGMA: {e}")
    return conn

def init_db():
    """Initializes the database schema with WAL mode enabled."""
    conn = get_connection()
    try:
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
        logger.info("Database schema initialized successfully.")
    finally:
        conn.close()

def create_session(title="New Chat"):
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now)
        )
        conn.commit()
        return {"id": session_id, "title": title}
    finally:
        conn.close()

def get_all_sessions():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
        sessions = [dict(row) for row in cursor.fetchall()]
        return sessions
    finally:
        conn.close()

def update_session_title(session_id: str, new_title: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (new_title, datetime.now().isoformat(), session_id))
        conn.commit()
    finally:
        conn.close()

import logging
logger = logging.getLogger("friday.memory.database")

def save_message(session_id: str, role: str, content: str):
    """Saves a message with automatic retry logic for transient locks."""
    max_retries = 3
    for attempt in range(max_retries):
        conn = None
        try:
            logger.info(f"Attempting to save {role} message (attempt {attempt+1})")
            msg_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, now)
            )
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            
            conn.commit()
            logger.info(f"Successfully committed message {msg_id} to DB.")
            return msg_id
            
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying save_message ({attempt+1}/{max_retries})...")
                time.sleep(1) # Wait for other process to finish
                continue
            logger.error(f"DB Operational Error in save_message: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"FATAL DB ERROR in save_message: {str(e)}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

def get_messages(session_id: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
        messages = [{"id": row["id"], "sender": row["role"], "text": row["content"], "created_at": row["created_at"]} for row in cursor.fetchall()]
        return messages
    finally:
        conn.close()

def delete_session(session_id: str):
    conn = get_connection()
    try:
        conn.cursor().execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.cursor().execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

def session_exists(session_id: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
        exists = cursor.fetchone() is not None
        return exists
    finally:
        conn.close()

# Initialize DB on import
init_db()
