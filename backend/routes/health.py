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
    """Simple health check returning subsystem status."""
    # LLM check
    llm_ok = "ok"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code != 200:
                llm_ok = "error"
    except Exception:
        llm_ok = "error"

    # STT check (piper/whisper availability)
    stt_ok = "ok"
    try:
        import os
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "piper.exe")):
            stt_ok = "degraded"
    except Exception:
        stt_ok = "error"

    return {
        "backend": "ok",
        "ws": "ok",
        "llm": llm_ok,
        "stt": stt_ok
    }

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
