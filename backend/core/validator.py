import os
import httpx
import sqlite3
import logging
from backend.config.settings import settings
from backend.core.logger import get_logger
from backend.memory.database import backup_database

logger = get_logger("core.validator")

class StartupValidator:
    """Verifies system integrity before F.R.I.D.A.Y. initializes."""

    @staticmethod
    async def validate_all():
        logger.info("Starting system integrity validation...")
        
        # 0. Backup DB
        backup_database()
        
        # 1. Check required folders
        folders = ["backend/memory", "backend/memory/chroma_db", "backend/tools", "backend/vision", "backend/voice"]
        for folder in folders:
            if not os.path.exists(folder):
                logger.warning(f"Creating missing directory: {folder}")
                os.makedirs(folder, exist_ok=True)

        # 2. Check Database
        try:
            conn = sqlite3.connect(settings.SQLITE_PATH)
            conn.execute("SELECT 1")
            conn.close()
            logger.info("SQLite database: HEALTHY")
        except Exception as e:
            logger.error(f"SQLite database: CORRUPT OR MISSING - {e}")
            return False

        # 3. Check Ollama Accessibility
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    logger.info("Ollama Service: REACHABLE")
                    
                    # 4. Check if model exists
                    models = [m["name"] for m in response.json().get("models", [])]
                    if any(settings.MODEL_NAME in m for m in models):
                        logger.info(f"Model '{settings.MODEL_NAME}': READY")
                    else:
                        logger.error(f"Model '{settings.MODEL_NAME}': NOT FOUND. Run 'ollama pull {settings.MODEL_NAME}'")
                        # We don't fail here, but we warn
                else:
                    logger.error(f"Ollama Service: UNEXPECTED STATUS {response.status_code}")
            except Exception as e:
                logger.error(f"Ollama Service: UNREACHABLE - {e}")
                # We don't fail hard, but F.R.I.D.A.Y will be limited

        logger.info("System integrity validation complete.")
        return True

validator = StartupValidator()
