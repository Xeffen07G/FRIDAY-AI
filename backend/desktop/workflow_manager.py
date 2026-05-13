import os
import subprocess
import pygetwindow as gw
from core.logger import get_logger
from memory.database import get_connection

logger = get_logger("desktop.workflow")

class WorkflowManager:
    """Manages project continuity, developer context, and research sessions."""

    def get_dev_context(self):
        """Detects active VS Code projects and git state."""
        context = {"projects": [], "git_status": {}}
        
        # 1. Detect VS Code windows
        vscode_wins = [w.title for w in gw.getWindowsWithTitle('Visual Studio Code')]
        for title in vscode_wins:
            # Title format: "filename - projectname - Visual Studio Code"
            parts = title.split(' - ')
            if len(parts) >= 3:
                project = parts[1]
                context["projects"].append(project)
        
        # 2. Check Git status of recently active projects (placeholder)
        return context

    def save_session(self, session_type, payload):
        """Persists a workflow session (research or coding) to memory."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_audit_log (component, action, payload) VALUES (?, ?, ?)",
                ("workflow_manager", f"SAVE_{session_type.upper()}", str(payload))
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
        finally:
            conn.close()

    def get_last_session(self, session_type):
        """Retrieves the most recent session for continuation."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload, timestamp FROM system_audit_log WHERE action = ? ORDER BY timestamp DESC LIMIT 1",
                (f"SAVE_{session_type.upper()}",)
            )
            row = cursor.fetchone()
            return row if row else None
        finally:
            conn.close()

workflow_manager = WorkflowManager()
