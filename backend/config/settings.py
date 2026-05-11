import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Central configuration for F.R.I.D.A.Y. backend using Pydantic Settings."""
    
    # App Settings
    APP_NAME: str = "F.R.I.D.A.Y. Core"
    VERSION: str = "1.2.0"
    DEBUG: bool = False
    
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
    
    # Database
    SQLITE_PATH: str = "friday_memory.db"
    CHROMA_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "chroma_db")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
