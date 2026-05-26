import os
import shutil
import logging
from typing import Dict, Any
from memory.database import DB_PATH, BACKUP_PATH

logger = logging.getLogger("friday.storage.backup_manager")

class BackupManager:
    """
    Coordinates platform profiles and memory snapshots.
    Schedules dynamic configuration backups and handles rollbacks to verify system continuity.
    """
    def __init__(self):
        self.snapshots_dir = "friday_snapshots"
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def create_runtime_snapshot(self, snapshot_name: str) -> str:
        """Captures copies of SQLite databases and configuration files."""
        logger.info(f"BackupManager: Creating runtime snapshot '{snapshot_name}'...")
        target_path = os.path.join(self.snapshots_dir, f"{snapshot_name}_db.bak")
        try:
            if os.path.exists(DB_PATH):
                shutil.copy(DB_PATH, target_path)
                logger.info(f"BackupManager: Snapshot compiled at '{target_path}'")
                return target_path
        except Exception as e:
            logger.error(f"BackupManager: Failed to compile snapshot: {e}")
        return ""

    def restore_snapshot(self, snapshot_name: str) -> bool:
        """Overwrites current SQLite targets with historical backup copies."""
        source_path = os.path.join(self.snapshots_dir, f"{snapshot_name}_db.bak")
        if not os.path.exists(source_path):
            logger.error(f"BackupManager: Snapshot source '{source_path}' does not exist.")
            return False
            
        try:
            shutil.copy(source_path, DB_PATH)
            logger.info("BackupManager: Successfully restored system snapshot state.")
            return True
        except Exception as e:
            logger.error(f"BackupManager: Rollback operation failed: {e}")
            return False

# Singleton instance
backup_manager = BackupManager()
