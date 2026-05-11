from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.orchestrator.orchestrator import friday_orchestrator
from backend.memory.database import session_exists
from backend.core.logger import get_logger
import uuid
import time

logger = get_logger("routes.chat")
router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    """
    Receives a message, sends it to the orchestrator, and returns the response stream.
    """
    request_id = str(uuid.uuid4())[:8]
    try:
        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty.")
            
        if not session_exists(req.session_id):
            raise HTTPException(status_code=404, detail="Session not found. Please refresh the page.")
            
        logger.info(f"[REQ:{request_id}] Received chat request (len: {len(req.message)})")
        
        return StreamingResponse(
            friday_orchestrator.process_stream(req.session_id, req.message, request_id, background_tasks),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REQ:{request_id}] Failed to initialize stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")