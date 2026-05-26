import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from memory.vector_store import vector_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

memories = vector_store.get_all_memories()
print(f"Total memories: {len(memories)}")
for m in memories:
    text = m["text"]
    if "color" in text.lower() or "colour" in text.lower() or "name" in text.lower():
        print(f"ID: {m['id']} | Text: {text} | Metadata: {m['metadata']}")
