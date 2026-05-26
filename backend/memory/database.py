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
        try:
            c.execute("ALTER TABLE messages ADD COLUMN request_nonce TEXT")
        except sqlite3.OperationalError:
            pass
            
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_msgs_nonce ON messages (session_id, request_nonce) WHERE request_nonce IS NOT NULL")
        try:
            c.execute("ALTER TABLE messages ADD COLUMN client_request_id TEXT")
        except sqlite3.OperationalError:
            pass
            
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_msgs_client_req ON messages (session_id, client_request_id) WHERE client_request_id IS NOT NULL")
        c.execute('''
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                client_request_id TEXT,
                state TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS desktop_files (
                path TEXT PRIMARY KEY,
                name TEXT,
                extension TEXT,
                size INTEGER,
                mtime DATETIME,
                last_indexed DATETIME
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS desktop_activity (
                id TEXT PRIMARY KEY,
                path TEXT,
                action TEXT,
                timestamp DATETIME
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS background_tasks (
                id TEXT PRIMARY KEY,
                name TEXT,
                payload TEXT,
                status TEXT,
                scheduled_at DATETIME,
                completed_at DATETIME,
                retries INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_audit_log (
                id TEXT PRIMARY KEY,
                event TEXT,
                component TEXT,
                metadata TEXT,
                timestamp DATETIME
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_dlq (
                id TEXT PRIMARY KEY,
                event TEXT,
                component TEXT,
                metadata TEXT,
                error TEXT,
                timestamp DATETIME
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS graph_edges (
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                temporal_weight REAL DEFAULT 1.0,
                updated_at DATETIME,
                PRIMARY KEY (source, target, relation),
                FOREIGN KEY (source) REFERENCES graph_nodes (id) ON DELETE CASCADE,
                FOREIGN KEY (target) REFERENCES graph_nodes (id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        logger.info("Database schema initialized successfully (including DLQ & Relational Graph tables).")
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

def save_message(session_id: str, role: str, content: str, request_nonce: str = None, client_request_id: str = None, message_id: str = None):
    """Saves a message with automatic retry logic for transient locks, exactly-once constraints, and cancel checks."""
    generation_id = client_request_id or request_nonce
    if generation_id:
        gen_state = get_generation_state(generation_id)
        if gen_state == "CANCELLED":
            logger.warning(f"[CANCEL_OWNERSHIP] Rejecting save_message for role {role} because generation {generation_id} is CANCELLED.")
            return "CANCELLED"
            
    if client_request_id is None:
        client_request_id = request_nonce
    if request_nonce is None:
        request_nonce = client_request_id
        
    max_retries = 3
    for attempt in range(max_retries):
        conn = None
        try:
            logger.info(f"Attempting to save {role} message (attempt {attempt+1}, nonce: {request_nonce}, client_request_id: {client_request_id}, message_id: {message_id})")
            msg_id = message_id if message_id else str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO messages (id, session_id, role, content, created_at, request_nonce, client_request_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, now, request_nonce, client_request_id)
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
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e).upper():
                logger.warning(f"Duplicate message suppressed by exactly-once constraint: nonce {request_nonce}, client_request_id {client_request_id}")
                return "DUPLICATE"
            logger.error(f"Integrity Error in save_message: {str(e)}", exc_info=True)
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

# Generation State Machine DB Helper Methods
def create_generation(generation_id: str, session_id: str, client_request_id: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT OR IGNORE INTO generations (id, session_id, client_request_id, state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (generation_id, session_id, client_request_id, "CREATED", now, now)
        )
        conn.commit()
        logger.info(f"[STATE_MACHINE] Generation {generation_id} CREATED for session {session_id}")
    finally:
        conn.close()

def update_generation_state(generation_id: str, state: str):
    """Transition state with exactly-once completion checks and terminal locks."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Get current state
        cursor.execute("SELECT state FROM generations WHERE id = ?", (generation_id,))
        row = cursor.fetchone()
        current_state = row[0] if row else None
        
        if not current_state:
            logger.warning(f"[STATE_MACHINE] Generation {generation_id} not found.")
            return False
            
        # EXACTLY-ONCE COMPLETION VALIDATION
        if state == "COMPLETED":
            if current_state != "STREAMING":
                logger.warning(f"[STATE_MACHINE] Invalid completion transition: {current_state} -> COMPLETED for {generation_id}")
                return False
                
        # Terminal state locks (Completed/Cancelled are final)
        if current_state in ["CANCELLED", "COMPLETED"]:
            if state in ["STREAMING", "ACCEPTED", "FAILED"]:
                logger.warning(f"[STATE_MACHINE] Blocked state transition from final {current_state} -> {state} for {generation_id}")
                return False
                
        cursor.execute(
            "UPDATE generations SET state = ?, updated_at = ? WHERE id = ?",
            (state, now, generation_id)
        )
        conn.commit()
        logger.info(f"[STATE_MACHINE] Generation {generation_id} transitioned: {current_state} -> {state}")
        return True
    finally:
        conn.close()

def get_generation_state(generation_id: str) -> str:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT state FROM generations WHERE id = ?", (generation_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def get_active_generation_id(session_id: str) -> str:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM generations WHERE session_id = ? AND state IN ('CREATED', 'ACCEPTED', 'STREAMING') ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()
