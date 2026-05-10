import sqlite3
from datetime import datetime

class SQLiteMemory:
    """Handles short-term and persistent conversational memory."""
    def __init__(self, db_path="friday_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        
    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT,
                assistant_response TEXT,
                timestamp DATETIME
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                actions TEXT
            )
        ''')
        self.conn.commit()
        
    def save_conversation(self, user_input: str, assistant_response: str):
        self.cursor.execute(
            "INSERT INTO conversations (user_input, assistant_response, timestamp) VALUES (?, ?, ?)",
            (user_input, assistant_response, datetime.now())
        )
        self.conn.commit()
        
    def get_recent_history(self, limit=5):
        self.cursor.execute(
            "SELECT user_input, assistant_response FROM conversations ORDER BY timestamp DESC LIMIT ?", 
            (limit,)
        )
        return self.cursor.fetchall()[::-1] # Reverse to get chronological order
