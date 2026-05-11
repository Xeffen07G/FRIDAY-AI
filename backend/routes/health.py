from fastapi import APIRouter
import psutil
import time
from backend.core.task_manager import task_manager
from backend.core.model_manager import model_manager
from backend.config.settings import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """System diagnostics for production monitoring."""
    
    # RAM Usage
    ram = psutil.virtual_memory()
    process = psutil.Process()
    process_ram = process.memory_info().rss / (1024 * 1024) # MB
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "system": {
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "ram_available_gb": round(ram.available / (1024**3), 2),
            "ram_percent": ram.percent,
            "friday_ram_mb": round(process_ram, 2)
        },
        "tasks": task_manager.get_diagnostics(),
        "models": model_manager.get_diagnostics(),
        "timestamp": time.time()
    }
