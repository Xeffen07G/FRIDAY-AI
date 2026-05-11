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
            "preference": re.compile(r"(like|love|prefer|favourite|favorite|hate|enjoy|dislike|don't like|do not like)", re.IGNORECASE),
            "personal": re.compile(r"(i am|my name|i live|i work|i am a|i was born|my birthday|my age)", re.IGNORECASE),
            "learning": re.compile(r"(learning|studying|reading|practicing|tutorial|course|degree|major)", re.IGNORECASE),
            "goal": re.compile(r"(my goal|i want to|i aim to|target|aspiration|dream|objective)", re.IGNORECASE),
            "project": re.compile(r"(building|creating|developing|coding|project|app|software)", re.IGNORECASE),
            "relationship": re.compile(r"(my wife|my husband|my friend|my boss|my colleague|my parent|my sibling)", re.IGNORECASE),
            "entertainment": re.compile(r"(movie|game|music|book|hobby|sport|team|band)", re.IGNORECASE),
            "location": re.compile(r"(travel|visit|went to|from|lives in|city|country)", re.IGNORECASE)
        }

    def _determine_category(self, text: str) -> str:
        for cat, pattern in self.category_patterns.items():
            if pattern.search(text):
                return cat
        return "context"

    async def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """Extracts and stores unique semantic memories with periodic cleanup."""
        clean_text = text.strip()
        if len(clean_text) < 12:
            return False
            
        try:
            # Periodic cleanup (every 20 stores approximately)
            if hasattr(self, '_store_count'):
                self._store_count += 1
            else:
                self._store_count = 1
                
            if self._store_count % 20 == 0:
                self.cleanup_old_memories()

            embedding = await embedding_service.get_embedding(clean_text)
            if not embedding:
                return False

            # 1. Duplicate/Similarity Check (Prevent redundant memories)
            existing = vector_store.search_memories(embedding, n_results=1)
            if existing and existing[0].get("distance", 1.0) < 0.2:
                logger.info(f"Memory Duplicate Detected (dist={existing[0]['distance']:.4f}). Skipping storage.")
                return False

            # 2. Importance Scoring (Enhanced heuristic)
            importance = 1.0
            high_priority = ["always", "never", "important", "essential", "must", "critical", "secret", "private"]
            medium_priority = ["usually", "often", "prefer", "like", "love", "hate", "goal", "target"]
            
            clean_lower = clean_text.lower()
            if any(word in clean_lower for word in high_priority):
                importance = 2.5
            elif any(word in clean_lower for word in medium_priority):
                importance = 1.8
            elif len(clean_text) > 200: # Long detailed context
                importance = 1.5

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

    def cleanup_old_memories(self, max_memories: int = 1000):
        """
        Prunes old, low-importance memories to keep the vector store efficient.
        """
        try:
            all_memories = vector_store.get_all_memories()
            if len(all_memories) <= max_memories:
                return
            
            logger.info(f"Starting memory cleanup. Current count: {len(all_memories)}")
            
            # Sort by: 1. Pinned (keep), 2. Importance (desc), 3. Recency (desc)
            # We want to delete the ones at the end of this list
            def sort_key(m):
                pinned = m["metadata"].get("pinned", False)
                importance = m["metadata"].get("importance", 1.0)
                created_at = m["metadata"].get("created_at", "1970-01-01")
                return (pinned, importance, created_at)
            
            all_memories.sort(key=sort_key, reverse=True)
            
            # Identify candidates for deletion (the bottom ones)
            to_delete = all_memories[max_memories:]
            for mem in to_delete:
                vector_store.delete_memory(mem["id"])
            
            logger.info(f"Memory cleanup complete. Deleted {len(to_delete)} memories.")
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")

    async def get_relevant_context(self, query: str, limit: int = 3):
        """Retrieves ranked relevant context."""
        trigger_keywords = ["remember", "recall", "earlier", "know about", "my", "preferences", "past", "history", "previous", "what", "who", "where", "tell me", "goal"]
        if not any(word in query.lower() for word in trigger_keywords):
            return ""

        try:
            embedding = await embedding_service.get_embedding(query)
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

    async def summarize_session(self, session_id: str, messages: list):
        """Generates a high-quality semantic summary using the LLM."""
        if len(messages) < 10:
            return False
            
        try:
            # Prepare transcript for LLM
            transcript = "\n".join([f"{'Assistant' if m['sender']=='friday' else 'User'}: {m['text']}" for m in messages])
            
            from backend.llm.ollama_client import LLMClient
            llm = LLMClient()
            
            system_prompt = "You are a master of semantic memory. Summarize the following conversation into a concise 'fact-based' summary of what was discussed, what the user's goals were, and any key personal info revealed. Keep it under 150 words."
            user_prompt = f"Transcript:\n{transcript}\n\nSummary:"
            
            summary = ""
            async for token in llm.generate_stream(user_prompt, system=system_prompt):
                summary += token
            
            if not summary.strip() or len(summary) < 20:
                return False

            embedding = await embedding_service.get_embedding(summary)
            if not embedding:
                return False

            metadata = {
                "session_id": session_id,
                "role": "assistant",
                "created_at": datetime.now().isoformat(),
                "category": "summary",
                "importance": 1.5,
                "pinned": False
            }
            
            logger.info(f"Generated semantic summary for session {session_id[:8]}")
            return vector_store.add_memory(str(uuid.uuid4()), summary, embedding, metadata)
        except Exception as e:
            logger.error(f"Session summarization failed: {e}")
            return False

memory_manager = MemoryManager()
