from fastapi import APIRouter
from backend.llm.ollama_client import LLMClient
from backend.memory.database import get_messages
from backend.memory.memory_manager import memory_manager
from backend.tools.tool_registry import tool_registry
import time

router = APIRouter()

@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "F.R.I.D.A.Y. Backend"}

@router.get("/health/deep")
async def deep_health_check():
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {}
    }
    
    # 1. Check LLM Connectivity
    try:
        llm = LLMClient()
        health_status["components"]["llm"] = {"status": "configured", "model": llm.model, "url": llm.base_url}
    except Exception as e:
        health_status["components"]["llm"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # 2. Check Tool Registry
    try:
        tools = tool_registry.get_all_tools_schema()
        health_status["components"]["tools"] = {"status": "active", "count": len(tools), "available": [t["name"] for t in tools]}
    except Exception as e:
        health_status["components"]["tools"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # 3. Check SQLite Database
    try:
        _ = get_messages("health_check_session_000")
        health_status["components"]["database"] = {"status": "active"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # 4. Check Vector DB
    try:
        col = memory_manager.collection
        if col:
            count = col.count()
            health_status["components"]["vector_db"] = {"status": "active", "memory_count": count}
        else:
            health_status["components"]["vector_db"] = {"status": "error", "error": "ChromaDB collection is None"}
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["vector_db"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status
