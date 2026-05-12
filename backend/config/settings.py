import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Central configuration for F.R.I.D.A.Y. backend using Pydantic Settings."""
    
    # App Settings
    APP_NAME: str = "F.R.I.D.A.Y. Core"
    VERSION: str = "1.5.0"
    DEBUG: bool = False
    
    # Runtime Paths (Production-grade Isolation)
    RUNTIME_BASE: str = "C:/Users/sayak/AI_RUNTIME"
    SQLITE_PATH: str = os.path.join(RUNTIME_BASE, "db", "friday_memory.db")
    CHROMA_PATH: str = os.path.join(RUNTIME_BASE, "chroma")
    LOG_FILE_PATH: str = os.path.join(RUNTIME_BASE, "logs", "friday.log")
    TEMP_AUDIO_PATH: str = os.path.join(RUNTIME_BASE, "temp")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    MODEL_NAME: str = "phi3:mini"
    OLLAMA_RETRY_COUNT: int = 3
    OLLAMA_TIMEOUT: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Memory Settings
    MEMORY_THRESHOLD: float = 0.55
    CONTEXT_WINDOW_SIZE: int = 8
    IMPORTANCE_THRESHOLD: float = 0.3
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure runtime directories exist upon import
for path in [os.path.dirname(settings.SQLITE_PATH), settings.CHROMA_PATH, os.path.dirname(settings.LOG_FILE_PATH), settings.TEMP_AUDIO_PATH]:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
