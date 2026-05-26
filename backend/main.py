import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.chat import router as chat_router
from routes.sessions import router as sessions_router
from routes.memories import router as memories_router
from routes.health import router as health_router
from routes.voice import router as voice_router
from routes.ws_voice import router as ws_voice_router
from routes.vision import router as vision_router
from routes.observability import router as observability_router
from config.settings import settings
from core.logger import setup_logging
from core.validator import validator
from core.task_manager import background_agent
from core.event_bus import event_bus
from core.context_engine import context_engine
from core.background_task_manager import background_task_manager
from tools.tool_scheduler import tool_scheduler
from desktop.tray_manager import tray_manager
from desktop.hotkey_manager import hotkey_manager

# Configure logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"F.R.I.D.A.Y. {settings.VERSION} initializing...")
    valid = await validator.validate_all()
    if not valid:
        logger.critical("Startup validation FAILED. System may be unstable.")
        
    try:
        from memory.vector_store import migrate_memories
        migrate_memories()
    except Exception as me:
        logger.error(f"Failed to run startup memory migration: {me}")
    
    # Start Runtimes
    await event_bus.start()
    await context_engine.start()
    await background_task_manager.start()
    from core.cognition_loop import cognition_loop
    await cognition_loop.start()
    await tool_scheduler.start()
    await background_agent.start()
    
    # Start Desktop UX threads
    tray_manager.start()
    hotkey_manager.start()
    
    logger.info("[WS_SERVER] Voice websocket mounted at /api/ws/voice")
    yield
    # Shutdown
    logger.info("Executing unified cancellation path for active sessions on shutdown...")
    from orchestrator.orchestrator import friday_orchestrator
    try:
        from core.runtime_state import runtime_state
        for session_id in list(runtime_state.conversations.keys()):
            await friday_orchestrator.cancel_generation(session_id)
    except Exception as se:
        logger.error(f"Error during unified cancel on backend shutdown: {se}")

    try:
        from memory.database import get_connection
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE generations SET state = 'CANCELLED', updated_at = ? WHERE state IN ('CREATED', 'ACCEPTED', 'STREAMING')",
            (datetime.now().isoformat(),)
        )
        conn.commit()
        conn.close()
        logger.info("All active generations marked as CANCELLED in DB on shutdown.")
    except Exception as dbe:
        logger.error(f"Error updating active generations to CANCELLED in DB on shutdown: {dbe}")

    await background_agent.stop()
    await tool_scheduler.stop()
    await cognition_loop.stop()
    await background_task_manager.stop()
    await context_engine.stop()
    await event_bus.stop()
    logger.info("F.R.I.D.A.Y. Core shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-hardened Local AI Assistant Core",
    version=settings.VERSION,
    lifespan=lifespan
)

# Exception Middleware
@app.middleware("http")
async def exception_handler(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error(f"[REQ:{request_id}] Unhandled Exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "F.R.I.D.A.Y. Core encountered an unhandled exception.",
                "detail": str(e),
                "request_id": request_id
            }
        )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register API Routes
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(memories_router, prefix="/api/memories", tags=["memories"])
app.include_router(health_router, prefix="/api/health", tags=["system"])
app.include_router(ws_voice_router, tags=["websocket"])
app.include_router(vision_router, prefix="/api/vision", tags=["vision"])
app.include_router(observability_router, prefix="/api/observability", tags=["observability"])

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Check for silent mode (from Autostart)
    is_silent = "--silent" in sys.argv
    if is_silent:
        logger.info("Starting in SILENT mode (minimized to tray).")
        # The frontend will handle this by checking the initial event state
    
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
