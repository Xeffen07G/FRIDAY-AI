from fastapi import APIRouter, HTTPException
from backend.memory.vector_store import vector_store

router = APIRouter()

@router.get("/")
def list_memories():
    """Retrieve all semantic memories."""
    return vector_store.get_all_memories()

@router.delete("/{memory_id}")
def delete_semantic_memory(memory_id: str):
    """Delete a semantic memory."""
    success = vector_store.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or failed to delete")
    return {"status": "deleted"}
