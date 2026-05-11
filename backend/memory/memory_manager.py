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

            return vector_store.add_memory(memory_id, text, embedding, metadata)
        except Exception as e:
            logger.error(f"Failed in memory storage: {e}")
            return False

    def get_relevant_context(self, query: str, limit: int = 3, threshold: float = 0.5):
        """
        Retrieves relevant memories. 
        Filters by threshold to prevent irrelevant hallucinations.
        """
        trigger_keywords = ["remember", "recall", "earlier", "know about", "my", "preferences", "past", "history", "previous", "what", "who", "where", "tell me"]
        if not any(word in query.lower() for word in trigger_keywords):
            return ""

        try:
            start_time = datetime.now()
            embedding = embedding_service.get_embedding(query)
            if not embedding:
                return ""

            raw_results = vector_store.search_memories(embedding, n_results=limit * 2)
            if not raw_results:
                return ""
            
            # Distance filtering: cosine distance < 0.5 is usually good
            filtered_results = [m for m in raw_results if m.get("distance", 1.0) < threshold]
            
            if not filtered_results:
                logger.debug(f"No memories passed threshold {threshold}")
                return ""

            now = datetime.now()
            ranked_results = []
            for mem in filtered_results:
                try:
                    created_at = datetime.fromisoformat(mem["metadata"]["created_at"])
                    days_old = (now - created_at).days
                    time_penalty = min(0.2, days_old * 0.005)
                except:
                    time_penalty = 0

                pinned_boost = -0.15 if mem["metadata"].get("pinned") else 0
                final_score = mem["distance"] + time_penalty + pinned_boost
                ranked_results.append((final_score, mem))

            ranked_results.sort(key=lambda x: x[0])
            top_memories = [x[1] for x in ranked_results[:limit]]
            
            context_strings = []
            for mem in top_memories:
                date_str = mem["metadata"].get("created_at", "")[:10]
                role = "User" if mem["metadata"].get("role") == "user" else "F.R.I.D.A.Y."
                # Added confidence indicator for LLM
                confidence = "HIGH" if mem["distance"] < 0.3 else "MEDIUM"
                context_strings.append(f"[Fact (Confidence: {confidence}) - {date_str}] {role}: {mem['text']}")
                
            return "\n".join(context_strings)
            
        except Exception as e:
            logger.error(f"Failed in memory retrieval: {e}")
            return ""

    def delete_session_memories(self, session_id: str):
        """Not yet implemented in vector store natively but can be filtered."""
        pass

memory_manager = MemoryManager()
