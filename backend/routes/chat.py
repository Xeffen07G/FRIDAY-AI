from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.orchestrator.orchestrator import Orchestrator
from backend.memory.database import session_exists
import logging
import uuid
import time

logger = logging.getLogger("friday.routes.chat")
router = APIRouter()
friday_orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    """
    Receives a message, sends it to the orchestrator, and returns the response.
    """
    try:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty.")
            
        if not session_exists(req.session_id):
            raise HTTPException(status_code=404, detail="Session not found. Please refresh the page.")
            
        logger.info(f"[REQ:{request_id}] Received chat request. Message preview: {req.message[:50]}...")
        
        # We pass request_id to process_stream for full lifecycle tracing
        orchestrator = Orchestrator()
        return StreamingResponse(
            orchestrator.process_stream(req.session_id, req.message, request_id, background_tasks),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")