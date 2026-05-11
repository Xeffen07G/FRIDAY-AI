import uuid
import logging
from datetime import datetime
from backend.memory.embedding_service import embedding_service
from backend.memory.vector_store import vector_store

logger = logging.getLogger("friday.memory.manager")

class MemoryManager:
    """Manages semantic memory extraction, storage, and context retrieval."""

    def __init__(self):
        logger.info("MemoryManager initialized.")
        
    @property
    def collection(self):
        """Exposes the vector collection for status checks and external tools."""
        return vector_store.collection

    def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """Extracts meaning and stores memory if valid."""
        if len(text.strip()) < 10:
            return False
            
        try:
            embedding = embedding_service.get_embedding(text)
            if not embedding:
                logger.warning("Embedding generation failed, falling back to skipping memory storage.")
                return False

            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            category = "context"
            lower_text = text.lower()
            if any(word in lower_text for word in ["i like", "i prefer", "my favorite", "always"]):
                category = "preference"
            elif any(word in lower_text for word in ["i am", "my name", "i live", "i work"]):
                category = "personal"
            elif any(word in lower_text for word in ["project", "build", "create", "app"]):
                category = "project"

            metadata = {
                "session_id": session_id,
                "role": role,
                "created_at": now,
                "category": category,
                "pinned": False
            }

            success = vector_store.add_memory(memory_id, text, embedding, metadata)
            if success:
                logger.info(f"Stored semantic memory {memory_id} (Category: {category})")
            return success
        except Exception as e:
            logger.error(f"Failed in memory storage pipeline: {e}")
            return False

    def get_relevant_context(self, query: str, limit: int = 3):
        """Retrieves and ranks relevant memories based on similarity and recency."""
        # Optimization: Only search memory if prompt suggests recall
        trigger_keywords = ["remember", "recall", "earlier", "know about", "my", "preferences", "past", "history", "previous"]
        if not any(word in query.lower() for word in trigger_keywords):
            return ""

        try:
            start_time = datetime.now()
            embedding = embedding_service.get_embedding(query)
            if not embedding:
                return ""

            raw_results = vector_store.search_memories(embedding, n_results=limit)
            if not raw_results:
                return ""
            
            retrieval_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Memory retrieval completed in {retrieval_ms:.2f}ms")

            now = datetime.now()
            ranked_results = []
            for mem in raw_results:
                try:
                    created_at = datetime.fromisoformat(mem["metadata"]["created_at"])
                    days_old = (now - created_at).days
                    time_penalty = min(0.3, days_old * 0.01)
                except:
                    time_penalty = 0

                pinned_boost = -0.2 if mem["metadata"].get("pinned") else 0
                
                final_score = mem["distance"] + time_penalty + pinned_boost
                ranked_results.append((final_score, mem))

            ranked_results.sort(key=lambda x: x[0])
            top_memories = [x[1] for x in ranked_results[:limit]]
            
            context_strings = []
            for mem in top_memories:
                date_str = mem["metadata"].get("created_at", "")[:10]
                role = "User" if mem["metadata"].get("role") == "user" else "F.R.I.D.A.Y."
                context_strings.append(f"[{date_str}] {role}: {mem['text']}")
                
            return "\n".join(context_strings)
            
        except Exception as e:
            logger.error(f"Failed in memory retrieval pipeline: {e}")
            return ""

memory_manager = MemoryManager()
