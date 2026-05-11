import logging
import sys
from backend.config.settings import settings

def setup_logging():
    """Initializes a structured logging system."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Root logger configuration
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silent noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.ERROR)
    
    logger = logging.getLogger("friday")
    logger.info(f"Logging initialized at level {settings.LOG_LEVEL}")
    return logger

def get_logger(name: str):
    """Returns a logger instance for a specific module."""
    return logging.getLogger(f"friday.{name}")

# Initialize on import if needed, or call from main.py
