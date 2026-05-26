import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("friday.core.session_recovery")

class SessionRecovery:
    """
    Maintains active session checkpoints across system restarts.
    Restores active workspaces, cursors, and resumes interrupted backgrounds.
    """
    def __init__(self):
        self.session_file = "friday_active_session.json"

    def save_checkpoint(self, active_workspace: str, cursor_line: int, pending_tasks: list):
        """Saves current interactive parameters before reboot sequence starts."""
        checkpoint = {
            "active_workspace": active_workspace,
            "cursor_line": cursor_line,
            "pending_tasks": pending_tasks
        }
        try:
            with open(self.session_file, "w") as f:
                json.dump(checkpoint, f)
            logger.info("SessionRecovery: Saved session checkpoint successfully.")
        except Exception as e:
            logger.error(f"SessionRecovery: Checkpoint save failed: {e}")

    def load_checkpoint(self) -> Dict[str, Any]:
        """Loads and returns active settings parameter snapshots."""
        if not os.path.exists(self.session_file):
            return {"active_workspace": None, "cursor_line": 1, "pending_tasks": []}
            
        try:
            with open(self.session_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"SessionRecovery: Checkpoint load failed: {e}")
            return {"active_workspace": None, "cursor_line": 1, "pending_tasks": []}

# Singleton instance
session_recovery = SessionRecovery()
