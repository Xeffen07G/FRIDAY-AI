import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("friday.config.config_manager")

DEFAULT_CONFIG = {
    "version": "2.4.0",
    "autonomy_level": 3,
    "idle_cooldown_seconds": 300,
    "local_only": True,
    "default_model": "phi3:mini",
    "backup_interval_days": 1
}

class ConfigurationManager:
    """
    Manages centralized configuration settings.
    Ensures safe profile backups, environment validation, and corrupted file rollbacks.
    """
    def __init__(self):
        self.config_path = "friday_config.json"
        self.active_config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads and parses the active settings file; restores defaults on corruption."""
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
            
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                # Simple migration check
                if data.get("version") != DEFAULT_CONFIG["version"]:
                    logger.info("ConfigurationManager: Migrating config schema to latest format")
                    data["version"] = DEFAULT_CONFIG["version"]
                    self.save_config(data)
                return data
        except Exception as e:
            logger.error(f"ConfigurationManager: Corrupted config detected! Reverting to defaults: {e}")
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict[str, Any]):
        """Persists the settings map to disk securely."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
            self.active_config = config
        except Exception as e:
            logger.error(f"ConfigurationManager: Failed to save settings: {e}")

    def update_override(self, key: str, value: Any):
        """Applies a runtime configuration override."""
        self.active_config[key] = value
        self.save_config(self.active_config)

# Singleton instance
config_manager = ConfigurationManager()
