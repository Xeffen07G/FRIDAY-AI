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
