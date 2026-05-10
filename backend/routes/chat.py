from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.orchestrator.orchestrator import Orchestrator
from backend.memory.database import session_exists
import logging

logger = logging.getLogger("friday.routes.chat")
router = APIRouter()
friday_orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Receives a message, sends it to the orchestrator, and returns the response.
    """
    try:
        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty.")
            
        if not session_exists(req.session_id):
            raise HTTPException(status_code=404, detail="Session not found. Please refresh the page.")
            
        logger.info(f"Received chat request: {req.message[:50]}...")
        
        return StreamingResponse(
            friday_orchestrator.process_stream(req.session_id, req.message), 
            media_type="text/plain"
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error during chat processing."
        )