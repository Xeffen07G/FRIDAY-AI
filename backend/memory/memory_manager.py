import uuid
import logging
import re
import time
from datetime import datetime
from backend.memory.embedding_service import embedding_service
from backend.memory.vector_store import vector_store
from backend.config.settings import settings

logger = logging.getLogger("friday.memory.manager")

class MemoryManager:
    """Advanced Memory System with duplicate detection and importance scoring."""

    def __init__(self):
        logger.info("MemoryManager initialized.")
        self.category_patterns = {
            "preference": re.compile(r"(like|love|prefer|favourite|favorite|hate|enjoy|dislike)", re.IGNORECASE),
            "personal": re.compile(r"(i am|my name|i live|i work|i am a|i was born)", re.IGNORECASE),
            "learning": re.compile(r"(learning|studying|reading|practicing|tutorial)", re.IGNORECASE),
            "goal": re.compile(r"(my goal|i want to|i aim to|target|aspiration)", re.IGNORECASE),
            "project": re.compile(r"(building|creating|developing|coding|project|app)", re.IGNORECASE)
        }

    def _determine_category(self, text: str) -> str:
        for cat, pattern in self.category_patterns.items():
            if pattern.search(text):
                return cat
        return "context"

    def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """Extracts and stores unique semantic memories."""
        clean_text = text.strip()
        if len(clean_text) < 12:
            return False
            
        try:
            embedding = embedding_service.get_embedding(clean_text)
            if not embedding:
                return False

            # 1. Duplicate/Similarity Check (Prevent redundant memories)
            existing = vector_store.search_memories(embedding, n_results=1)
            if existing and existing[0].get("distance", 1.0) < 0.2:
                logger.info(f"Memory Duplicate Detected (dist={existing[0]['distance']:.4f}). Skipping storage.")
                return False

            # 2. Importance Scoring (Basic heuristic)
            importance = 1.0
            if any(word in clean_text.lower() for word in ["always", "never", "important", "essential", "must"]):
                importance = 2.0

            memory_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            category = self._determine_category(clean_text)
            
            metadata = {
                "session_id": session_id,
                "role": role,
                "created_at": now,
                "category": category,
                "pinned": False,
                "importance": importance
            }

            return vector_store.add_memory(memory_id, clean_text, embedding, metadata)
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    def get_relevant_context(self, query: str, limit: int = 3):
        """Retrieves ranked relevant context."""
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
            
            threshold = settings.MEMORY_THRESHOLD
            filtered_results = [m for m in raw_results if m.get("distance", 1.0) < threshold]
            
            if not filtered_results:
                return ""

            # Rank by Distance + Importance + Recency
            now_ts = time.time()
            ranked_results = []
            for mem in filtered_results:
                try:
                    # Importance boost
                    importance = float(mem["metadata"].get("importance", 1.0))
                    imp_boost = (importance - 1.0) * -0.1 # Lower distance is better
                    
                    # Recency penalty
                    created_at = datetime.fromisoformat(mem["metadata"]["created_at"])
                    age_days = (datetime.now() - created_at).days
                    recency_penalty = min(0.2, age_days * 0.005)
                except:
                    imp_boost = 0
                    recency_penalty = 0

                final_score = mem["distance"] + imp_boost + recency_penalty
                ranked_results.append((final_score, mem))

            ranked_results.sort(key=lambda x: x[0])
            top_memories = [x[1] for x in ranked_results[:limit]]
            
            return "\n".join([f"[{m['metadata'].get('category', 'context').upper()}] {m['text']}" for m in top_memories])
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return ""

    def summarize_session(self, session_id: str, messages: list):
        """Generates a semantic summary of a session and stores it."""
        if len(messages) < 5:
            return False
            
        try:
            # Simple heuristic summary for now (first and last few messages)
            # In a real agentic setup, we would call the LLM to summarize
            text_to_summarize = " ".join([m["text"] for m in messages if m["sender"] == "user"])
            summary = f"Summary of session {session_id[:8]}: {text_to_summarize[:200]}..."
            
            embedding = embedding_service.get_embedding(summary)
            if not embedding:
                return False

            metadata = {
                "session_id": session_id,
                "role": "assistant",
                "created_at": datetime.now().isoformat(),
                "category": "summary",
                "importance": 1.5
            }
            
            return vector_store.add_memory(str(uuid.uuid4()), summary, embedding, metadata)
        except Exception as e:
            logger.error(f"Session summarization failed: {e}")
            return False

memory_manager = MemoryManager()
