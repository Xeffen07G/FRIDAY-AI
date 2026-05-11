import uuid
import logging
import re
from datetime import datetime
from backend.memory.embedding_service import embedding_service
from backend.memory.vector_store import vector_store
from backend.config.settings import settings

logger = logging.getLogger("friday.memory.manager")

class MemoryManager:
    """Manages semantic memory extraction, storage, and context retrieval."""

    def __init__(self):
        logger.info("MemoryManager initialized.")
        self.category_maps = {
            "preference": re.compile(r"(like|love|prefer|favourite|favorite|hate|enjoy|dislike|always want)", re.IGNORECASE),
            "personal": re.compile(r"(i am|my name|i live|i work|i am a|i am an|my age|i was born)", re.IGNORECASE),
            "learning": re.compile(r"(learning|studying|reading|practicing|trying to understand|course|tutorial)", re.IGNORECASE),
            "goal": re.compile(r"(my goal|i want to|i aim to|i plan to|i am going to|target|aspiration)", re.IGNORECASE),
            "project": re.compile(r"(building|creating|developing|coding|project|app|website|software)", re.IGNORECASE),
            "entertainment": re.compile(r"(movie|film|show|series|game|book|music|band|artist|video)", re.IGNORECASE)
        }

    def _determine_category(self, text: str) -> str:
        lower_text = text.lower()
        for category, pattern in self.category_maps.items():
            if pattern.search(lower_text):
                return category
        return "context"

    def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """Extracts semantic meaning and stores it in vector storage."""
        clean_text = text.strip()
        if len(clean_text) < 10 or len(clean_text.split()) < 3:
            return False
            
        try:
            embedding = embedding_service.get_embedding(clean_text)
            if not embedding:
                return False

            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            category = self._determine_category(clean_text)
            
            metadata = {
                "session_id": session_id,
                "role": role,
                "created_at": now,
                "category": category,
                "pinned": False,
                "importance": 1.0 # Default importance
            }

            return vector_store.add_memory(memory_id, clean_text, embedding, metadata)
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            return False

    def get_relevant_context(self, query: str, limit: int = 3):
        """Retrieves and ranks relevant memories."""
        # Trigger keywords for retrieval
        trigger_keywords = ["remember", "recall", "earlier", "know about", "my", "preferences", "past", "history", "previous", "what", "who", "where", "tell me", "goal"]
        if not any(word in query.lower() for word in trigger_keywords):
            return ""

        try:
            embedding = embedding_service.get_embedding(query)
            if not embedding:
                return ""

            raw_results = vector_store.search_memories(embedding, n_results=limit * 2)
            if not raw_results:
                return ""
            
            # Filter by distance using setting
            threshold = settings.MEMORY_THRESHOLD
            filtered_results = [m for m in raw_results if m.get("distance", 1.0) < threshold]
            
            if not filtered_results:
                return ""

            now = datetime.now()
            ranked_results = []
            for mem in filtered_results:
                try:
                    created_at = datetime.fromisoformat(mem["metadata"]["created_at"])
                    days_old = (now - created_at).days
                    recency_score = min(0.15, days_old * 0.005)
                except:
                    recency_score = 0

                final_score = mem["distance"] + recency_score
                ranked_results.append((final_score, mem))

            ranked_results.sort(key=lambda x: x[0])
            top_memories = [x[1] for x in ranked_results[:limit]]
            
            context_strings = []
            for mem in top_memories:
                date_str = mem["metadata"].get("created_at", "")[:10]
                category = mem["metadata"].get("category", "info")
                context_strings.append(f"[{category.upper()} - {date_str}] {mem['text']}")
                
            return "\n".join(context_strings)
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return ""

    def optimize_memory(self):
        """Cleanup routine for old or low-importance memories."""
        try:
            all_memories = vector_store.get_all_memories()
            # Logic for deleting old memories could go here
            logger.info(f"Memory optimization triggered. Scanning {len(all_memories)} memories.")
            return True
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False

memory_manager = MemoryManager()
