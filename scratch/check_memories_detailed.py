import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from memory.vector_store import vector_store
memories = vector_store.get_all_memories()
print(f"Total memories in ChromaDB: {len(memories)}")
for i, m in enumerate(memories):
    print(f"[{i}] ID: {m['id']}")
    print(f"    Text: {m['text']}")
    print(f"    Metadata: {m['metadata']}")
