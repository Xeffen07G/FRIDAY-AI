from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.memory.database import get_all_sessions, create_session, get_messages

router = APIRouter()

class SessionCreate(BaseModel):
    title: str = "New Chat"

@router.get("")
def list_sessions():
    """Retrieve all chat sessions."""
    return get_all_sessions()

@router.post("")
def create_new_session(req: SessionCreate):
    """Create a new chat session."""
    return create_session(req.title)

@router.get("/{session_id}/messages")
def list_messages(session_id: str):
    """Get all messages for a specific session."""
    return get_messages(session_id)

class SessionUpdate(BaseModel):
    title: str

@router.delete("/{session_id}")
def delete_chat_session(session_id: str):
    from backend.memory.database import session_exists, delete_session
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id)
    return {"status": "deleted"}

@router.put("/{session_id}")
def update_chat_session(session_id: str, req: SessionUpdate):
    from backend.memory.database import session_exists, update_session_title
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    update_session_title(session_id, req.title)
    return {"status": "updated", "title": req.title}
