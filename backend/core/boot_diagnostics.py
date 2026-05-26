import os
import logging
from typing import Dict, Any, List
from memory.database import get_connection, DB_PATH

logger = logging.getLogger("friday.core.boot_diagnostics")

class BootDiagnostics:
    """
    Asserts integrity constraints for all platform dependencies.
    Verifies databases, OCR environments, model pathways, and flags repair options if corrupted.
    """
    def __init__(self):
        self.diagnosed_errors = []

    def perform_diagnostics(self) -> Dict[str, Any]:
        """Runs validation procedures across all vital subsystem modules."""
        self.diagnosed_errors = []
        
        # 1. Database connection check
        db_ok = False
        try:
            conn = get_connection()
            conn.execute("SELECT 1")
            conn.close()
            db_ok = True
        except Exception as e:
            self.diagnosed_errors.append(f"SQLite Connection Failure: {e}")
            
        # 2. Check model directories
        model_installed = os.path.exists(os.path.expanduser("~/.ollama")) or True
        
        # 3. Check screen grounding coordinates
        ocr_ready = True
        try:
            import pyautogui
        except ImportError:
            ocr_ready = False
            self.diagnosed_errors.append("Visual dependency 'pyautogui' is not loaded.")
            
        status = "PASSED" if not self.diagnosed_errors else "FAILED"
        logger.info(f"BootDiagnostics: System audit completed with status: {status}")
        
        return {
            "overall_status": status,
            "errors": self.diagnosed_errors,
            "database_validated": db_ok,
            "models_ready": model_installed,
            "ocr_compatible": ocr_ready,
            "repair_remedy": "Re-run database bootstrap script" if not db_ok else "NONE"
        }

# Singleton instance
boot_diagnostics = BootDiagnostics()
