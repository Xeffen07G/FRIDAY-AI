from fastapi import APIRouter
import psutil
import time
import sys
from core.task_manager import task_manager
from core.model_manager import model_manager
from config.settings import settings

from memory.vector_store import vector_store

router = APIRouter()
START_TIME = time.time()

@router.get("/")
async def health_check():
    """Simple health check."""
    return {"status": "healthy", "timestamp": time.time()}

@router.get("/deep")
async def deep_health_check():
    """System diagnostics for production monitoring."""
    
    # RAM Usage
    ram = psutil.virtual_memory()
    process = psutil.Process()
    process_ram = process.memory_info().rss / (1024 * 1024) # MB
    
    # Vector DB Status
    vdb_count = 0
    vdb_status = "error"
    try:
        if vector_store.collection:
            vdb_count = vector_store.collection.count()
            vdb_status = "healthy"
    except:
        pass

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "uptime": round(time.time() - START_TIME, 2),
        "ollama": {
            "status": "online" if model_manager._active_models else "standby",
            "active_model": settings.MODEL_NAME
        },
        "system": {
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "ram_available_gb": round(ram.available / (1024**3), 2),
            "ram_percent": ram.percent,
            "friday_ram_mb": round(process_ram, 2)
        },
        "vector_db": {
            "status": vdb_status,
            "memory_count": vdb_count
        },
        "tasks": task_manager.get_diagnostics(),
        "models": model_manager.get_diagnostics(),
        "desktop": {
            "startup_mode": "silent" if "--silent" in sys.argv else "normal",
            "autostart_enabled": True # Placeholder for registry check
        },
        "timestamp": time.time()
    }
