import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routes.chat import router as chat_router
from backend.routes.sessions import router as sessions_router
from backend.routes.memories import router as memories_router
from backend.routes.health import router as health_router
from backend.routes.voice import router as voice_router
from backend.routes.vision import router as vision_router
from backend.config.settings import settings
from backend.core.logger import setup_logging
from backend.core.validator import validator

# Configure logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"F.R.I.D.A.Y. {settings.VERSION} initializing...")
    valid = await validator.validate_all()
    if not valid:
        logger.critical("Startup validation FAILED. System may be unstable.")
    yield
    # Shutdown
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

# Register routes
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(memories_router, prefix="/api/memories", tags=["memories"])
app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(vision_router, prefix="/api/vision", tags=["vision"])

@app.get("/")
def read_root():
    return {"status": "online", "identity": "F.R.I.D.A.Y."}
