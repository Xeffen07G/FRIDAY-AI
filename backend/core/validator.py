import os
import httpx
import sqlite3
import logging
from config.settings import settings
from core.logger import get_logger
from memory.database import backup_database

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

        # 3. Check Dependencies (FFMPEG / Piper)
        import shutil
        if not shutil.which("ffmpeg"):
            logger.error("FFMPEG: NOT FOUND in PATH. Realtime audio will fail.")
            # return False # Fail hard if critical
        else:
            logger.info("FFMPEG: READY")
            
        piper_path = os.path.join(os.getcwd(), "piper.exe")
        if not os.path.exists(piper_path):
            logger.warning(f"PIPER TTS: NOT FOUND at {piper_path}. Voice response will be disabled.")
        else:
            logger.info("PIPER TTS: READY")

        # 4. Check Ollama Accessibility
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    logger.info("Ollama Service: REACHABLE")
                    
                    models = [m["name"] for m in response.json().get("models", [])]
                    if any(settings.MODEL_NAME in m for m in models):
                        logger.info(f"Primary Model '{settings.MODEL_NAME}': READY")
                    else:
                        logger.error(f"Primary Model '{settings.MODEL_NAME}': NOT FOUND. Run 'ollama pull {settings.MODEL_NAME}'")
                else:
                    logger.error(f"Ollama Service: ERROR STATUS {response.status_code}")
            except Exception as e:
                logger.error(f"Ollama Service: UNREACHABLE - {e}")

        # 5. Check Desktop Agent Dependencies
        try:
            import pygetwindow
            import watchdog
            import pyperclip
            logger.info("Desktop Dependencies: READY")
        except ImportError as e:
            logger.error(f"Desktop Dependencies: MISSING ({e}). Desktop Agent will be disabled.")

        # 6. Check Environment Secrets
        required_keys = ["TAVILY_API_KEY"]
        for key in required_keys:
            if not os.getenv(key):
                logger.warning(f"Production Key '{key}': MISSING. Some tools will be restricted.")

        logger.info("System integrity validation complete.")
        return True

validator = StartupValidator()
