import uuid
import logging
import re
from datetime import datetime
from backend.memory.embedding_service import embedding_service
from backend.memory.vector_store import vector_store

logger = logging.getLogger("friday.memory.manager")

class MemoryManager:
    """Manages semantic memory extraction, storage, and context retrieval."""

    def __init__(self):
        logger.info("MemoryManager initialized.")
        # Patterns for categorizing memories
        self.category_maps = {
            "preference": re.compile(r"(like|love|prefer|favourite|favorite|hate|enjoy|dislike|always want)", re.IGNORECASE),
            "personal": re.compile(r"(i am|my name|i live|i work|i am a|i am an|my age|i was born)", re.IGNORECASE),
            "learning": re.compile(r"(learning|studying|reading|practicing|trying to understand|course|tutorial)", re.IGNORECASE),
            "goal": re.compile(r"(my goal|i want to|i aim to|i plan to|i am going to|target|aspiration)", re.IGNORECASE),
            "project": re.compile(r"(building|creating|developing|coding|project|app|website|software)", re.IGNORECASE),
            "entertainment": re.compile(r"(movie|film|show|series|game|book|music|band|artist|video)", re.IGNORECASE)
        }

    @property
    def collection(self):
        """Exposes the vector collection for status checks."""
        return vector_store.collection

    def _determine_category(self, text: str) -> str:
        """Heuristic categorization based on keywords."""
        lower_text = text.lower()
        for category, pattern in self.category_maps.items():
            if pattern.search(lower_text):
                return category
        return "context"

    def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """
        Extracts semantic meaning and stores it. 
        Filters out short/irrelevant text.
        """
        clean_text = text.strip()
        if len(clean_text) < 10 or len(clean_text.split()) < 3:
            return False
            
        try:
            # 1. Generate Embedding
            embedding = embedding_service.get_embedding(clean_text)
            if not embedding:
                logger.error("Memory Extraction: Failed to generate embedding.")
                return False

            # 2. Assign Metadata
            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            category = self._determine_category(clean_text)
            
            metadata = {
                "session_id": session_id,
                "role": role,
                "created_at": now,
                "category": category,
                "pinned": False,
                "confidence": 1.0 # Base confidence for direct user statements
            }

            # 3. Store in Vector DB
            success = vector_store.add_memory(memory_id, clean_text, embedding, metadata)
            if success:
                logger.info(f"Memory Persisted: [{category}] {memory_id} - '{clean_text[:50]}...'")
            return success
            
        except Exception as e:
            logger.error(f"Memory Extraction Pipeline Failed: {e}", exc_info=True)
            return False

    def get_relevant_context(self, query: str, limit: int = 3, threshold: float = 0.55):
        """
        Retrieves relevant memories with distance-based thresholding.
        Higher threshold (0.55) to allow more semantic flexibility.
        """
        # Trigger keywords for retrieval
        trigger_keywords = ["remember", "recall", "earlier", "know about", "my", "preferences", "past", "history", "previous", "what", "who", "where", "tell me", "goal"]
        if not any(word in query.lower() for word in trigger_keywords):
            return ""

        try:
            start_time = datetime.now()
            embedding = embedding_service.get_embedding(query)
            if not embedding:
                return ""

            # Search with slightly higher n_results to allow for filtering
            raw_results = vector_store.search_memories(embedding, n_results=limit * 2)
            if not raw_results:
                return ""
            
            # Filter by cosine distance
            filtered_results = [m for m in raw_results if m.get("distance", 1.0) < threshold]
            
            if not filtered_results:
                logger.debug(f"Retrieval: No memories passed threshold {threshold}")
                return ""

            # Rank by combined score (Distance + Recency)
            now = datetime.now()
            ranked_results = []
            for mem in filtered_results:
                try:
                    created_at = datetime.fromisoformat(mem["metadata"]["created_at"])
                    days_old = (now - created_at).days
                    # Recency boost: newer memories are slightly preferred
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
                context_strings.append(f"[Past {category.capitalize()} - {date_str}] {mem['text']}")
                
            return "\n".join(context_strings)
            
        except Exception as e:
            logger.error(f"Memory Retrieval Failed: {e}")
            return ""

memory_manager = MemoryManager()
