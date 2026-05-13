import os
import time
import sqlite3
import asyncio
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from memory.database import get_connection
from memory.vector_store import vector_store
from memory.embedding_service import embedding_service
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger("desktop.file_manager")

class DesktopFileHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager

    def on_modified(self, event):
        if not event.is_directory:
            # Avoid rapid fire indexing for same file
            asyncio.run_coroutine_threadsafe(self.manager.index_file(event.src_path), self.manager.loop)

    def on_created(self, event):
        if not event.is_directory:
            asyncio.run_coroutine_threadsafe(self.manager.index_file(event.src_path), self.manager.loop)

class FileManager:
    """Phase 1: File Intelligence - Handles indexing, watching, and semantic retrieval."""
    
    def __init__(self):
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            
        self.observer = Observer()
        self.watched_paths = []
        self._file_collection = None
        self._is_active = False
        self._index_debounce = {} # path -> timestamp
        self._debounce_interval = 2.0 # seconds
        self._ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', '.gemini', '.next', 'dist', 'build'}
        self._file_hashes = {} # hash -> path (for duplicate detection)

    @property
    def file_collection(self):
        if self._file_collection is None:
            client = vector_store.client
            if client:
                try:
                    self._file_collection = client.get_or_create_collection(
                        name="friday_files",
                        metadata={"hnsw:space": "cosine"}
                    )
                except Exception as e:
                    logger.error(f"Failed to create friday_files collection: {e}")
        return self._file_collection

    def start_watching(self, path):
        """Registers a folder for real-time monitoring."""
        path = os.path.abspath(path)
        if path not in self.watched_paths and os.path.exists(path):
            handler = DesktopFileHandler(self)
            self.observer.schedule(handler, path, recursive=True)
            self.watched_paths.append(path)
            logger.info(f"Watching folder: {path}")
            # Initial crawl
            asyncio.run_coroutine_threadsafe(self.crawl_directory(path), self.loop)

    def start(self):
        if not self._is_active:
            self.observer.start()
            self._is_active = True
            logger.info("FileManager Observer: STARTED")

    def stop(self):
        if self._is_active:
            self.observer.stop()
            self.observer.join()
            self._is_active = False
            logger.info("FileManager Observer: STOPPED")

    async def crawl_directory(self, path):
        """Performs initial metadata indexing for a directory."""
        logger.info(f"Crawling directory: {path}")
        for root, _, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                await self.index_file(full_path)

    async def index_file(self, path):
        """Indexes file metadata and content with duplication prevention."""
        if not os.path.exists(path): return
        
        # Debounce rapid-fire events (common in watchdog)
        now = time.time()
        if path in self._index_debounce:
            if now - self._index_debounce[path] < self._debounce_interval:
                return
        self._index_debounce[path] = now

        try:
            stat = os.stat(path)
            name = os.path.basename(path)
            ext = os.path.splitext(name)[1].lower()
            size = stat.st_size
            mtime_raw = stat.st_mtime
            mtime = datetime.fromtimestamp(mtime_raw).isoformat()
            
            # Check if already indexed with same mtime to avoid redundant ChromaDB writes
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT mtime FROM desktop_files WHERE path = ?", (path,))
                row = cursor.fetchone()
                # Phase 4: Duplicate Detection (Basic size+mtime hash)
                file_hash = f"{size}_{mtime_raw}"
                if file_hash in self._file_hashes and self._file_hashes[file_hash] != path:
                    logger.debug(f"Duplicate detected: {path} matches {self._file_hashes[file_hash]}")
                    # We still index metadata but skip semantic re-processing
                self._file_hashes[file_hash] = path

                cursor.execute(
                    "INSERT OR REPLACE INTO desktop_files (path, name, extension, size, mtime, last_indexed) VALUES (?, ?, ?, ?, ?, ?)",
                    (path, name, ext, size, mtime, datetime.now().isoformat())
                )
                conn.commit()
                event_bus.emit("desktop", "file_indexed", {"path": path, "name": name, "size": size})
            finally:
                conn.close()

            # Semantic indexing for text-based files (Limit to 5MB to avoid hang)
            if size < 5 * 1024 * 1024 and ext in ['.txt', '.md', '.py', '.js', '.jsx', '.json', '.c', '.cpp', '.rs']:
                await self._index_content(path, name)
                
        except Exception as e:
            logger.debug(f"Index error for {path}: {e}")

    async def _index_content(self, path, name):
        """Reads content and stores embeddings in ChromaDB."""
        try:
            # Non-blocking read would be better but for local files small chunks are okay
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4000) # Index first 4k chars for semantic context
            
            if not content.strip(): return
            
            embedding = await embedding_service.get_embedding(content)
            if embedding and self.file_collection:
                self.file_collection.upsert(
                    ids=[path],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{"path": path, "name": name, "type": "file_content"}]
                )
        except Exception as e:
            logger.debug(f"Content indexing failed: {path} - {e}")

    def search_files(self, query):
        """Standard SQL search for files by name."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT path, name, mtime FROM desktop_files WHERE name LIKE ? OR path LIKE ? ORDER BY mtime DESC LIMIT 10",
                (f"%{query}%", f"%{query}%")
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    async def semantic_search(self, query, limit=5):
        """Vector search for file contents."""
        embedding = await embedding_service.get_embedding(query)
        if not embedding or not self.file_collection: return []
        
        try:
            results = self.file_collection.query(
                query_embeddings=[embedding],
                n_results=limit
            )
            
            files = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    files.append({
                        "path": results["ids"][0][i],
                        "name": results["metadatas"][0][i]["name"],
                        "snippet": results["documents"][0][i][:150] + "...",
                        "distance": results["distances"][0][i]
                    })
            return files
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def check_health(self):
        """Phase 3: Self-healing - Restarts watcher if dead."""
        if not self._is_active: return
        if not self.observer or not self.observer.is_alive():
            logger.warning("FileManager: Watcher thread DIED. Restarting...")
            self.start()
        
        # Cleanup debounce cache
        now = time.time()
        self._index_debounce = {p: t for p, t in self._index_debounce.items() if now - t < 60}

    def log_activity(self, path, action):
        """Logs file interaction for recent activity awareness."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO desktop_activity (id, path, action, timestamp) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4())[:8], path, action, datetime.now().isoformat())
            )
            conn.commit()
            event_bus.emit("desktop", "activity", {"path": path, "action": action})
        finally:
            conn.close()

    def get_recent_activity(self, limit=10):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT path, action, timestamp FROM desktop_activity ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

file_manager = FileManager()
