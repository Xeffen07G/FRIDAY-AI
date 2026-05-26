import logging
from typing import Dict, Any

logger = logging.getLogger("friday.core.safe_mode")

class SafeModeRuntime:
    """
    Enforces restricted recovery boundaries.
    Disables OCR steps, terminal overrides, and blocks active workflow loops during emergencies.
    """
    def __init__(self):
        self.safe_mode_active = False

    def trigger_emergency_safe_mode(self):
        """Locks down dynamic operational controllers to maintain sandbox constraints."""
        self.safe_mode_active = True
        logger.warning("SafeModeRuntime: Emergency recovery sandbox activated! Autonomous systems locked.")

    def deactivate_safe_mode(self):
        self.safe_mode_active = False
        logger.info("SafeModeRuntime: Emergency recovery deactivated. Restoring runtime systems.")

    def block_operational_actions(self, action_type: str) -> bool:
        """Determines if a planned step must be blocked based on emergency mode."""
        if self.safe_mode_active:
            if action_type in ["terminal_command", "mouse_click", "file_delete", "ocr_scan"]:
                logger.warning(f"SafeModeRuntime: Blocked unsafe action '{action_type}' due to safe-mode locks.")
                return True
        return False

# Singleton instance
safe_mode_runtime = SafeModeRuntime()
