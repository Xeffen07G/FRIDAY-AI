import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.chat import router as chat_router
from backend.routes.sessions import router as sessions_router
from backend.routes.memories import router as memories_router
from backend.routes.health import router as health_router
from backend.config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("friday.main")

# Initialize the FastAPI Application
app = FastAPI(
    title="F.R.I.D.A.Y. Backend",
    description="Minimal stable Local AI Assistant Core API",
    version="1.0.0"
)

# Proper CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register our routes
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(sessions_router, prefix="/api", tags=["sessions"])
app.include_router(memories_router, prefix="/api", tags=["memories"])
app.include_router(health_router, prefix="/api", tags=["health"])

@app.get("/")
def read_root():
    return {"message": "F.R.I.D.A.Y. API is online. Use /api/chat to communicate."}
