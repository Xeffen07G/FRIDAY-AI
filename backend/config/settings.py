import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Central configuration for F.R.I.D.A.Y. backend."""
    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "phi3:mini")
    OLLAMA_RETRY_COUNT: int = 2
    OLLAMA_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Memory Settings
    MEMORY_THRESHOLD: float = 0.55
    CONTEXT_WINDOW_SIZE: int = 6
    
    # Database
    SQLITE_PATH: str = "friday.db"
    CHROMA_PATH: str = "memory/chroma_db"

settings = Settings()
