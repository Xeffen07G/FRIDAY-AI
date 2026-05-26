import chromadb
import logging
import os

logger = logging.getLogger("friday.memory.vector_store")

class VectorStore:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        self._client = None
        self._collection = None
        logger.info(f"VectorStore initialized with path: {self.db_path} (Lazy loading enabled)")

    @property
    def client(self):
        if self._client is None:
            try:
                logger.info("Initializing ChromaDB PersistentClient...")
                self._client = chromadb.PersistentClient(path=self.db_path)
                logger.info("ChromaDB PersistentClient successfully initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB PersistentClient: {e}", exc_info=True)
                return None
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            client = self.client
            if client:
                try:
                    logger.info("Loading or creating ChromaDB collection 'friday_memories'...")
                    self._collection = client.get_or_create_collection(
                        name="friday_memories",
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info("ChromaDB collection 'friday_memories' is active.")
                except Exception as e:
                    logger.error(f"Failed to get or create ChromaDB collection: {e}", exc_info=True)
                    return None
        return self._collection

    def add_memory(self, memory_id: str, text: str, embedding: list, metadata: dict):
        if not self.collection:
            return False
        try:
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add memory to vector store: {e}")
            return False

    def search_memories(self, query_embedding: list, n_results=5):
        if not self.collection:
            return []
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            memories = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    memories.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else 0
                    })
            return memories
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    def update_metadata(self, memory_id: str, metadata: dict):
        if not self.collection:
            return False
        try:
            self.collection.update(ids=[memory_id], metadatas=[metadata])
            return True
        except Exception as e:
            logger.error(f"Failed to update memory metadata: {e}")
            return False

    def delete_memory(self, memory_id: str):
        if not self.collection:
            return False
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    def get_all_memories(self):
        if not self.collection:
            return []
        try:
            results = self.collection.get()
            memories = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    memories.append({
                        "id": results["ids"][i],
                        "text": results["documents"][i],
                        "metadata": results["metadatas"][i]
                    })
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve all memories: {e}")
            return []

vector_store = VectorStore()


def migrate_memories():
    try:
        from datetime import datetime
        memories = vector_store.get_all_memories()
        logger.info(f"[MIGRATION] Retrieved {len(memories)} memories for migration.")
        
        profile_keys = {"favorite_color", "dog_name", "name", "birthday", "favorite_movie", "favorite_food", "favorite_song"}
        
        # 1. Parse/normalize canonical keys and legacy formats first
        for mem in memories:
            meta = mem.get("metadata", {})
            text = mem.get("text", "")
            
            # Extract canonical_key and value if missing
            if not meta.get("canonical_key"):
                from orchestrator.orchestrator import parse_storage_input
                canonical, val = parse_storage_input(text)
                if canonical:
                    meta["canonical_key"] = canonical
                    meta["value"] = val
                else:
                    lower_text = text.lower()
                    if "color is" in lower_text or "colour is" in lower_text:
                        meta["canonical_key"] = "favorite_color"
                        words = lower_text.split()
                        meta["value"] = words[-1].strip(".!?") if words else "unknown"
                    elif "name is" in lower_text:
                        if "dog" in lower_text:
                            meta["canonical_key"] = "dog_name"
                            meta["value"] = "max" if "max" in lower_text else "rocky" if "rocky" in lower_text else "unknown"
                        else:
                            meta["canonical_key"] = "name"
                            meta["value"] = "sayak" if "sayak" in lower_text else "unknown"
                    else:
                        meta["canonical_key"] = "unknown"
                        meta["value"] = text
            
            if "user_id" not in meta:
                meta["user_id"] = "default_user"
            if "session_id" not in meta:
                meta["session_id"] = "default_session"
            if "created_at" not in meta:
                meta["created_at"] = datetime.now().isoformat()
            if "source" not in meta:
                meta["source"] = "migrated"
            if "active" not in meta:
                meta["active"] = True
            elif isinstance(meta["active"], str):
                meta["active"] = (meta["active"].lower() == "true")
            if "superseded_by" not in meta:
                meta["superseded_by"] = "none"
                
            vector_store.update_metadata(mem["id"], meta)

        # Re-fetch memories with populated metadata
        memories = vector_store.get_all_memories()
        
        profile_groups = {}      
        conv_groups = {}         
        
        for mem in memories:
            meta = mem.get("metadata", {})
            canonical = meta.get("canonical_key")
            if not canonical or canonical == "unknown":
                continue
                
            scope = "profile" if canonical in profile_keys else "conversation"
            meta["scope"] = scope
            
            if scope == "profile":
                if canonical not in profile_groups:
                    profile_groups[canonical] = []
                profile_groups[canonical].append(mem)
            else:
                session_id = meta.get("session_id", "default_session")
                group_key = (session_id, canonical)
                if group_key not in conv_groups:
                    conv_groups[group_key] = []
                conv_groups[group_key].append(mem)

        # Helper to sort by created_at desc and update status
        def deduplicate_group(group_list):
            if len(group_list) <= 1:
                if len(group_list) == 1:
                    mem = group_list[0]
                    meta = mem.get("metadata", {})
                    meta["active"] = True
                    meta["superseded_by"] = "none"
                    vector_store.update_metadata(mem["id"], meta)
                return
                
            # Sort desc
            group_list.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
            
            newest = group_list[0]
            newest_meta = newest.get("metadata", {})
            newest_meta["active"] = True
            newest_meta["superseded_by"] = "none"
            vector_store.update_metadata(newest["id"], newest_meta)
            
            for old_mem in group_list[1:]:
                old_meta = old_mem.get("metadata", {})
                old_meta["active"] = False
                old_meta["superseded_by"] = newest["id"]
                vector_store.update_metadata(old_mem["id"], old_meta)
                logger.info(f"[MIGRATION] Superseded old memory ID={old_mem['id']} with newest ID={newest['id']}")

        # Deduplicate profile
        for canonical, group in profile_groups.items():
            deduplicate_group(group)
            
        # Deduplicate conversation
        for group_key, group in conv_groups.items():
            deduplicate_group(group)
            
        logger.info("[MIGRATION] Database vector memories migration completed successfully.")
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
