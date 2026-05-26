import chromadb

def check_db(path):
    print(f"=== CHECKING CHROMA DB PATH: {path} ===")
    try:
        client = chromadb.PersistentClient(path=path)
        collections = client.list_collections()
        print(f"Collections: {[c.name for c in collections]}")
        for col_name in [c.name for c in collections]:
            col = client.get_collection(col_name)
            results = col.get()
            print(f"Collection '{col_name}' has {len(results['ids'])} items:")
            for i in range(len(results['ids'])):
                print(f"  [{i}] ID: {results['ids'][i]} | Document: {results['documents'][i]} | Metadata: {results['metadatas'][i]}")
    except Exception as e:
        print(f"Error checking {path}: {e}")

check_db("C:/Users/sayak/AI_RUNTIME/chroma")
import os
check_db(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/memory/chroma_db")))
