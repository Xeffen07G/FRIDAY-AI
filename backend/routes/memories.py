from fastapi import APIRouter, HTTPException, Body
from memory.vector_store import vector_store
from typing import Dict, Any

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

@router.patch("/{memory_id}")
def update_semantic_memory(memory_id: str, updates: Dict[str, Any] = Body(...)):
    """Update metadata for a specific memory (e.g. category, importance)."""
    # Fetch existing to avoid wiping other metadata
    all_mems = vector_store.get_all_memories()
    target = next((m for m in all_mems if m["id"] == memory_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    new_metadata = target["metadata"].copy()
    new_metadata.update(updates)
    
    success = vector_store.update_metadata(memory_id, new_metadata)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update memory")
        
    return {"status": "updated", "id": memory_id, "metadata": new_metadata}
