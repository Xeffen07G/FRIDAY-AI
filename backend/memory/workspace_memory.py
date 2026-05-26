import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from memory.database import get_connection

logger = logging.getLogger("friday.memory.workspace_memory")

class WorkspaceMemoryManager:
    """
    Task 4: Workspace Memory
    Governs SQLite schemas for workspace timelines, coding sessions, git branches, 
    recently opened files, and terminal logs. Resolves recovery queries.
    """
    def __init__(self):
        self._init_table()

    def _init_table(self):
        conn = get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_memory (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    git_repo TEXT,
                    git_branch TEXT,
                    last_worked_on TEXT NOT NULL,
                    terminal_history TEXT,
                    recent_files TEXT,
                    research_sessions TEXT
                )
            """)
            conn.commit()
            
            # Check if table is empty to pre-seed with premium mock workspaces
            cursor = conn.execute("SELECT COUNT(*) FROM workspace_memory")
            count = cursor.fetchone()[0]
            if count == 0:
                now = datetime.now().isoformat()
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                
                # 1. Frontend Workspace
                conn.execute(
                    """
                    INSERT INTO workspace_memory (id, project_name, project_path, git_repo, git_branch, last_worked_on, terminal_history, recent_files, research_sessions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "jarvis_frontend",
                        "JARVIS React Frontend",
                        "C:\\Users\\sayak\\Downloads\\JARVIS\\frontend",
                        "JARVIS",
                        "main",
                        now,
                        json.dumps(["npm run dev", "npm install"]),
                        json.dumps(["src/components/EngineeringHub.jsx", "src/App.jsx", "vite.config.js"]),
                        json.dumps(["Investigating websocket port reconciliation on port 8000"])
                    )
                )
                
                # 2. AI Research Workspace
                conn.execute(
                    """
                    INSERT INTO workspace_memory (id, project_name, project_path, git_repo, git_branch, last_worked_on, terminal_history, recent_files, research_sessions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "ai_research",
                        "Transformers AI Research Lab",
                        "C:\\Users\\sayak\\Documents\\AI_Research",
                        "transformers-experiments",
                        "dev/attention-decay",
                        yesterday,
                        json.dumps(["python train.py", "git pull origin main"]),
                        json.dumps(["attention_decay.py", "README.md", "environment.yml"]),
                        json.dumps(["Analyzing attention head performance on long sequence lengths"])
                    )
                )
                conn.commit()
                logger.info("Workspace memory pre-seeded with premium developer environments.")
        except Exception as e:
            logger.error(f"Workspace Memory Table Init Failed: {e}")
        finally:
            conn.close()

    def record_workspace_session(self, project_path: str, project_name: str, git_repo: Optional[str] = None, git_branch: Optional[str] = None, recent_files: List[str] = None, terminal_command: Optional[str] = None, research_context: Optional[str] = None):
        """Records or updates a coding/workspace session in SQLite."""
        conn = get_connection()
        try:
            # Check if project_path exists
            cursor = conn.execute("SELECT id, recent_files, terminal_history, research_sessions FROM workspace_memory WHERE project_path = ?", (project_path,))
            row = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            # File list processing
            files_list = recent_files or []
            term_history = [terminal_command] if terminal_command else []
            research_logs = [research_context] if research_context else []
            
            if row:
                ws_id = row[0]
                # Merge existing files and terminal commands
                try:
                    exist_files = json.loads(row[1] or "[]")
                    files_list = list(dict.fromkeys(files_list + exist_files))[:20]
                except Exception:
                    pass
                    
                try:
                    exist_term = json.loads(row[2] or "[]")
                    term_history = list(dict.fromkeys(term_history + exist_term))[:10]
                except Exception:
                    pass

                try:
                    exist_res = json.loads(row[3] or "[]")
                    research_logs = list(dict.fromkeys(research_logs + exist_res))[:5]
                except Exception:
                    pass
                
                conn.execute(
                    """
                    UPDATE workspace_memory 
                    SET project_name = ?, git_repo = ?, git_branch = ?, last_worked_on = ?, recent_files = ?, terminal_history = ?, research_sessions = ?
                    WHERE id = ?
                    """,
                    (project_name, git_repo, git_branch, now, json.dumps(files_list), json.dumps(term_history), json.dumps(research_logs), ws_id)
                )
            else:
                ws_id = project_name.lower().replace(" ", "_")
                conn.execute(
                    """
                    INSERT INTO workspace_memory (id, project_name, project_path, git_repo, git_branch, last_worked_on, terminal_history, recent_files, research_sessions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ws_id, project_name, project_path, git_repo, git_branch, now, json.dumps(term_history), json.dumps(files_list), json.dumps(research_logs))
                )
            conn.commit()
            logger.info(f"Workspace recorded: {project_name} at {project_path}")
        except Exception as e:
            logger.error(f"Failed to record workspace: {e}")
        finally:
            conn.close()

    def get_workspace_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns workspace logs sorted by last worked on date."""
        conn = get_connection()
        history = []
        try:
            cursor = conn.execute(
                "SELECT project_name, project_path, git_repo, git_branch, last_worked_on, recent_files, terminal_history, research_sessions FROM workspace_memory ORDER BY last_worked_on DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                history.append({
                    "project_name": row[0],
                    "project_path": row[1],
                    "git_repo": row[2],
                    "git_branch": row[3],
                    "last_worked_on": row[4],
                    "recent_files": json.loads(row[5] or "[]"),
                    "terminal_history": json.loads(row[6] or "[]"),
                    "research_sessions": json.loads(row[7] or "[]")
                })
        except Exception as e:
            logger.error(f"Failed to retrieve workspace history: {e}")
        finally:
            conn.close()
        return history

    def query_workspace(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parses commands like:
        - 'continue my frontend work'
        - 'restore yesterday's AI research'
        - 'open the repo I worked on last night'
        Matches with project titles, dates, or terms.
        """
        lower_q = query.lower()
        history = self.get_workspace_history(limit=10)
        if not history:
            return None

        # Direct sort matching
        if "last night" in lower_q or "recently" in lower_q or "last worked on" in lower_q or "continue my work" in lower_q:
            return history[0]

        # Keyword matching
        for ws in history:
            name = ws["project_name"].lower()
            path = ws["project_path"].lower()
            repo = (ws["git_repo"] or "").lower()
            
            # Simple keyword search
            if "frontend" in lower_q and ("frontend" in name or "frontend" in path or "frontend" in repo):
                return ws
            if "backend" in lower_q and ("backend" in name or "backend" in path or "backend" in repo):
                return ws
            if "research" in lower_q and ("research" in name or "research" in path or "research" in repo):
                return ws
            if "ai" in lower_q and ("ai" in name or "ai" in path or "ai" in repo):
                return ws

        # Fallback to the latest active workspace
        return history[0]

# Singleton instance
workspace_memory = WorkspaceMemoryManager()
