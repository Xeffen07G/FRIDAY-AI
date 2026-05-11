import asyncio
from sentence_transformers import SentenceTransformer
import os
from functools import lru_cache
from backend.core.logger import get_logger

logger = get_logger("memory.embedding")

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.initialized = False
        self._lock = asyncio.Lock()

    async def _initialize(self):
        if not self.initialized:
            async with self._lock:
                if not self.initialized:
                    try:
                        logger.info(f"Loading embedding model: {self.model_name}")
                        # Load model in a thread to avoid blocking the main event loop
                        self.model = await asyncio.to_thread(SentenceTransformer, self.model_name)
                        self.initialized = True
                        return True
                    except Exception as e:
                        logger.error(f"Failed to load embedding model: {e}")
                        return False
        return True

    @lru_cache(maxsize=2000)
    def _get_embedding_sync(self, text: str):
        """Internal synchronous encoding call for thread offloading."""
        if not self.initialized:
            return None
        return self.model.encode(text).tolist()

    async def get_embedding(self, text: str):
        """Public API for generating embeddings with async offloading."""
        if not text or not text.strip():
            return None
            
        if not self.initialized:
            await self._initialize()
            
        try:
            # Check lru_cache via a wrapper or direct call in thread
            # Since encode is CPU heavy, we always offload it
            return await asyncio.to_thread(self._get_embedding_sync, text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def get_embeddings_batch(self, texts: list):
        """Generates embeddings for multiple texts in one batch."""
        if not texts:
            return []
            
        if not self.initialized:
            await self._initialize()
            
        try:
            # Offload batch encoding to thread
            embeddings = await asyncio.to_thread(self.model.encode, texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return []

embedding_service = EmbeddingService()
