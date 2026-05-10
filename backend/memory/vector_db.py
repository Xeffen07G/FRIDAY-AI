import chromadb

class VectorMemory:
    """Handles semantic search and long-term project memory using ChromaDB."""
    def __init__(self, persist_dir="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name="friday_memory")
        
    def add_memory(self, text: str, metadata: dict = None, memory_id: str = None):
        """Stores a new memory embedded in vector space."""
        if not memory_id:
            import uuid
            memory_id = str(uuid.uuid4())
            
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {"type": "general"}],
            ids=[memory_id]
        )
        return memory_id
        
    def search_memory(self, query: str, n_results: int = 3):
        """Retrieves most relevant memories based on semantic similarity."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results.get("documents", [[]])[0]
