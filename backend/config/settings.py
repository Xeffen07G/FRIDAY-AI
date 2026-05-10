import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Settings:
    """Central configuration for F.R.I.D.A.Y. backend."""
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen2.5:3b")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS: list = ["*"]  # Restrict in production

settings = Settings()
