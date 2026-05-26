import json
import logging
from typing import Dict, Any, List, Optional
from memory.database import get_connection

logger = logging.getLogger("friday.memory.operational_memory")

class OperationalMemory:
    """
    Saves successful visual layouts, command patterns, failure frequencies, 
    and preferred recovery sequences inside SQLite to adapt to custom workspaces.
    """
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """Initializes tables for persistent operational learning metrics."""
        conn = get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    status TEXT NOT NULL, -- SUCCESS, FAILED
                    run_details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_ui_patterns (
                    pattern_key TEXT PRIMARY KEY,
                    layout_coordinates TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            logger.info("OperationalMemory: Schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to create operational memory tables: {e}")
        finally:
            conn.close()

    def log_workflow_run(self, name: str, status: str, details: Dict[str, Any]):
        """Logs a workflow execution run for future pattern scoring."""
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO operational_workflow_runs (workflow_name, status, run_details) VALUES (?, ?, ?)",
                (name, status, json.dumps(details))
            )
            conn.commit()
            logger.info(f"OperationalMemory: Workflow run logged successfully ({name} &rarr; {status}).")
        except Exception as e:
            logger.error(f"Failed to log workflow run: {e}")
        finally:
            conn.close()

    def save_ui_pattern(self, key: str, coordinates: Dict[str, Any]):
        """Stores element location patterns to avoid repetitive OCR sweeps."""
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO operational_ui_patterns (pattern_key, layout_coordinates) VALUES (?, ?)",
                (key, json.dumps(coordinates))
            )
            conn.commit()
            logger.info(f"OperationalMemory: Saved UI element coordinate pattern for: {key}")
        except Exception as e:
            logger.error(f"Failed to save UI pattern: {e}")
        finally:
            conn.close()

    def get_ui_pattern(self, key: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.execute("SELECT layout_coordinates FROM operational_ui_patterns WHERE pattern_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"Failed to query UI pattern: {e}")
        finally:
            conn.close()
        return None

# Singleton instance
operational_memory = OperationalMemory()
