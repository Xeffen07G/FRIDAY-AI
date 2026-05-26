import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from memory.vector_store import vector_store
memories = vector_store.get_all_memories()
print(f"Total memories in ChromaDB: {len(memories)}")
for m in memories:
    print(f"ID: {m['id']} | Text: {m['text']} | Metadata: {m['metadata']}")
