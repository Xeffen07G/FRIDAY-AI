import os
import shutil
import logging
from typing import Dict, Any
from memory.database import backup_database, DB_PATH

logger = logging.getLogger("friday.storage.storage_manager")

class StorageManager:
    """
    Ensures safe offline data durability.
    Enforces SQLite storage limits and schedules automated hot-backup rotations.
    """
    def __init__(self):
        self.quota_bytes = 500 * 1024 * 1024  # 500 MB limit

    def verify_storage_quotas(self) -> Dict[str, Any]:
        """Calculates current workspace storage sizes relative to user quotas."""
        db_size = 0
        if os.path.exists(DB_PATH):
            db_size = os.path.getsize(DB_PATH)
            
        utilization = db_size / self.quota_bytes
        logger.info(f"StorageManager: Active SQLite database size: {round(db_size / (1024*1024), 2)}MB ({round(utilization * 100, 1)}% of quota)")
        
        return {
            "database_bytes": db_size,
            "quota_bytes": self.quota_bytes,
            "utilization_percent": round(utilization * 100, 2),
            "quota_exceeded": utilization >= 1.0
        }

    def execute_scheduled_backup(self) -> bool:
        """Invokes hot backup api routines to safeguard SQLite profiles."""
        logger.info("StorageManager: Triggering automated hot backup cycle...")
        try:
            backup_database()
            return True
        except Exception as e:
            logger.error(f"StorageManager: Backup generation failed: {e}")
            return False

# Singleton instance
storage_manager = StorageManager()
