from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from orchestrator.orchestrator import friday_orchestrator
from memory.database import session_exists, create_generation, get_generation_state
from core.logger import get_logger
import uuid
import time

logger = get_logger("routes.chat")
router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    nonce: str = None

@router.post("/")
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
            
        if req.nonce:
            # Check duplicate request send before uvicorn stream triggers
            existing_state = get_generation_state(req.nonce)
            if existing_state is not None:
                logger.warning(f"[REQ:{request_id}] Dropping duplicate request (nonce: {req.nonce})")
                raise HTTPException(status_code=409, detail="Duplicate request dropped by exactly-once constraint")
            
            # Persist state machine CREATED state
            create_generation(req.nonce, req.session_id, req.nonce)
            
        logger.info(f"[REQ:{request_id}] Received chat request (len: {len(req.message)}, nonce: {req.nonce})")
        
        return StreamingResponse(
            friday_orchestrator.process_stream(req.session_id, req.message, request_id, req.nonce, background_tasks),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REQ:{request_id}] Failed to initialize stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/settings/stable")
async def toggle_stable_mode(enabled: bool):
    """
    Toggles the production Stable Mode (Production Lock Mode).
    """
    from core.runtime_state import runtime_state
    runtime_state.system.stable_mode = enabled
    runtime_state.save_to_disk()
    logger.info(f"Stable Mode configured to: {enabled}")
    return {"status": "success", "stable_mode": enabled}

@router.post("/settings/performance")
async def toggle_performance_mode(enabled: bool):
    """
    Toggles high-performance/responsiveness mode.
    """
    from core.runtime_state import runtime_state
    if not hasattr(runtime_state.system, "performance_mode"):
        runtime_state.system.performance_mode = False
    runtime_state.system.performance_mode = enabled
    runtime_state.save_to_disk()
    logger.info(f"Performance Mode configured to: {enabled}")
    return {"status": "success", "performance_mode": enabled}

class CancelRequest(BaseModel):
    session_id: str

@router.post("/cancel")
async def cancel_endpoint(req: CancelRequest):
    """
    Unified cancel endpoint routing through cancel_generation()
    """
    logger.warning(f"Unified cancellation endpoint hit for session {req.session_id}")
    await friday_orchestrator.cancel_generation(req.session_id)
    return {"status": "success"}

