import uuid
import logging
import re
import time
from datetime import datetime
from memory.embedding_service import embedding_service
from memory.vector_store import vector_store
from config.settings import settings

logger = logging.getLogger("friday.memory.manager")

class MemoryManager:
    """Hierarchical Cognitive Memory System with decay and compression."""

    def __init__(self):
        logger.info("Cognitive Memory System initialized.")
        self.category_patterns = {
            "profile": re.compile(r"(i am|my name|i live|i work|i am a|i was born|my birthday|my age|my goal|my preference|i like|i hate)", re.IGNORECASE),
            "episodic": re.compile(r"(remember when|last time|yesterday|earlier|previously|the other day)", re.IGNORECASE),
            "semantic": re.compile(r"(is a|definition|what is|how does|fact|knowledge|concept)", re.IGNORECASE),
            "project": re.compile(r"(building|creating|developing|coding|project|app|software|task)", re.IGNORECASE)
        }

    def _determine_type(self, text: str) -> str:
        """Determines if memory is 'working', 'episodic', 'semantic', or 'profile'."""
        lower_text = text.lower()
        for m_type, pattern in self.category_patterns.items():
            if pattern.search(lower_text):
                return m_type
        return "working"

    async def extract_and_store_memory(self, text: str, role: str, session_id: str):
        """Extracts and stores unique memories with importance-based decay."""
        clean_text = text.strip()
        if len(clean_text) < 15: return False
            
        try:
            embedding = await embedding_service.get_embedding(clean_text)
            if not embedding: return False

            # Similarity Check (Deduplication)
            existing = vector_store.search_memories(embedding, n_results=1)
            if existing and existing[0].get("distance", 1.0) < 0.15:
                logger.debug("Redundant memory suppressed.")
                return False

            m_type = self._determine_type(clean_text)
            
            # Base importance by type
            importance_map = {"profile": 3.0, "project": 2.2, "semantic": 1.8, "episodic": 1.5, "working": 1.0}
            importance = importance_map.get(m_type, 1.0)
            
            # Contextual reinforcement
            if any(word in clean_text.lower() for word in ["important", "remember", "never forget", "critical"]):
                importance += 1.0

            memory_id = str(uuid.uuid4())
            now = datetime.now()
            
            metadata = {
                "session_id": session_id,
                "role": role,
                "created_at": now.isoformat(),
                "type": m_type,
                "importance": importance,
                "access_count": 1,
                "last_accessed": now.isoformat(),
                "decay_rate": 0.05 if m_type == "working" else 0.01
            }

            return vector_store.add_memory(memory_id, clean_text, embedding, metadata)
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return False

    def run_memory_decay(self, max_memories: int = 2000):
        """Prunes low-importance memories that have aged/decayed."""
        try:
            all_memories = vector_store.get_all_memories()
            if len(all_memories) <= max_memories: return

            now = datetime.now()
            scored_memories = []
            
            for m in all_memories:
                meta = m["metadata"]
                created_at = datetime.fromisoformat(meta["created_at"])
                age_days = (now - created_at).days
                
                # Decay Formula: base_importance - (age * decay_rate) + (log(access_count))
                import math
                access_count = meta.get("access_count", 1)
                decay_rate = meta.get("decay_rate", 0.02)
                
                final_score = meta["importance"] - (age_days * decay_rate) + (math.log(access_count) * 0.2)
                scored_memories.append((final_score, m["id"]))

            scored_memories.sort(key=lambda x: x[0])
            to_delete = scored_memories[:len(all_memories) - max_memories]
            
            for score, mid in to_delete:
                vector_store.delete_memory(mid)
            
            logger.info(f"Decay Engine: Pruned {len(to_delete)} stale memories.")
        except Exception as e:
            logger.error(f"Memory decay failed: {e}")

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

            # Rank by Distance + Importance + Recency + Type Boost
            now_ts = time.time()
            ranked_results = []
            for mem in filtered_results:
                try:
                    meta = mem["metadata"]
                    # Importance boost
                    importance = float(meta.get("importance", 1.0))
                    imp_boost = (importance - 1.0) * -0.15 # Lower distance is better
                    
                    # Type boost
                    m_type = meta.get("type", "working")
                    type_boost = -0.1 if m_type in ["profile", "project"] else 0
                    
                    # Recency penalty (less severe for profile/semantic)
                    created_at = datetime.fromisoformat(meta["created_at"])
                    age_days = (datetime.now() - created_at).days
                    age_factor = 0.002 if m_type in ["profile", "semantic"] else 0.01
                    recency_penalty = min(0.3, age_days * age_factor)
                except:
                    imp_boost, type_boost, recency_penalty = 0, 0, 0

                final_score = mem["distance"] + imp_boost + type_boost + recency_penalty
                ranked_results.append((final_score, mem))

            ranked_results.sort(key=lambda x: x[0])
            top_memories = [x[1] for x in ranked_results[:limit]]
            
            # Update access count for retrieved memories (Heat mapping)
            for m in top_memories:
                mid = m["id"]
                try:
                    m["metadata"]["access_count"] = m["metadata"].get("access_count", 0) + 1
                    m["metadata"]["last_accessed"] = datetime.now().isoformat()
                    vector_store.update_metadata(mid, m["metadata"])
                except: pass

            return "\n".join([f"[{m['metadata'].get('type', 'working').upper()}] {m['text']}" for m in top_memories])
            
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
            
            from llm.ollama_client import LLMClient
            llm = LLMClient()
            
            system_prompt = "You are a master of semantic memory. Summarize the following conversation into a concise 'fact-based' summary of what was discussed, what the user's goals were, and any key personal info revealed. Keep it under 150 words."
            user_prompt = f"Transcript:\n{transcript}\n\nSummary:"
            
            messages_to_send = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            summary = ""
            async for token in llm.generate_stream(messages_to_send):
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

    async def save_prior_action(self, action_type: str, payload: dict, success: bool, session_id: str):
        """Saves a prior executed action into episodic memory and SQL audit logs."""
        import json
        action_text = f"Executed action {action_type} with payload {json.dumps(payload)}. Success: {success}."
        await self.extract_and_store_memory(action_text, "assistant", session_id)
        
        from memory.database import get_connection
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO system_audit_log (id, event, component, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), f"ACTION_{action_type.upper()}", "executor", json.dumps({"payload": payload, "success": success}), datetime.now().isoformat())
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to log action to SQLite audit log: {e}")
        finally:
            conn.close()

    async def save_preference(self, key: str, value: str, session_id: str):
        """Saves user preference explicitly to profile semantic memory."""
        pref_text = f"User preference: {key} is set to {value}."
        await self.extract_and_store_memory(pref_text, "user", session_id)

    async def save_workflow(self, workflow_name: str, steps: list, session_id: str):
        """Saves a reusable workflow pattern to project semantic memory."""
        import json
        wf_text = f"Saved workflow '{workflow_name}' consisting of steps: {json.dumps(steps)}."
        await self.extract_and_store_memory(wf_text, "user", session_id)

memory_manager = MemoryManager()

