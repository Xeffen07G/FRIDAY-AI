import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat, sessions, memories
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
app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api/sessions")
app.include_router(memories.router, prefix="/api/memories")

@app.get("/health")
def health_check():
    """Health check endpoint to verify backend is running."""
    logger.debug("Health check requested.")
    return {"status": "ok", "service": "F.R.I.D.A.Y. Backend"}

@app.get("/")
def read_root():
    return {"message": "F.R.I.D.A.Y. API is online. Use /api/chat to communicate."}
