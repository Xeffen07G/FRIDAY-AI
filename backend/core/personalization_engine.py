import logging
from typing import Dict, Any, List

logger = logging.getLogger("friday.core.personalization")

class PersonalizationEngine:
    """
    Manages custom ergonomics parameters.
    Saves preferred editors, terminal shells, and adjusts notification tolerances silently.
    """
    def __init__(self):
        self.preferred_editor = "VSCode"
        self.notification_tolerance = "BALANCED"
        self.trusted_terminals = ["powershell", "cmd"]

    def retrieve_ergonomic_presets(self) -> Dict[str, Any]:
        """Provides user specific workflow settings to adjust planner step compiling."""
        return {
            "preferred_editor": self.preferred_editor,
            "notification_tolerance": self.notification_tolerance,
            "trusted_terminals": self.trusted_terminals,
            "theme_mode": "dark"
        }

    def update_presets(self, key: str, value: Any):
        if hasattr(self, key):
            setattr(self, key, value)
            logger.info(f"PersonalizationEngine: Ergonomic parameter '{key}' updated to: {value}")

# Singleton instance
personalization_engine = PersonalizationEngine()
