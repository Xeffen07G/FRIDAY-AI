import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routes.chat import router as chat_router
from backend.routes.sessions import router as sessions_router
from backend.routes.memories import router as memories_router
from backend.routes.health import router as health_router
from backend.config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("friday.main")

app = FastAPI(
    title="F.R.I.D.A.Y. Core",
    description="Production-hardened Local AI Assistant Core",
    version="1.1.0"
)

# Exception Middleware
@app.middleware("http")
async def exception_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled Exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "F.R.I.D.A.Y. Core encountered an unhandled exception.", "detail": str(e)}
        )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(memories_router, prefix="/api", tags=["memories"])
app.include_router(health_router, prefix="/api", tags=["health"])

@app.get("/")
def read_root():
    return {"status": "online", "identity": "F.R.I.D.A.Y."}
