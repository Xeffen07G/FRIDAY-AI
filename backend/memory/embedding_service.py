import logging
from sentence_transformers import SentenceTransformer
import os
from functools import lru_cache

logger = logging.getLogger("friday.memory.embedding")

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.initialized = False

    def _initialize(self):
        if not self.initialized:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self.initialized = True
                return True
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}", exc_info=True)
                return False
        return True

    @lru_cache(maxsize=1000)
    def _get_cached_embedding(self, text: str):
        """Internal cached embedding call."""
        if not self.initialized:
            if not self._initialize():
                return None
        return self.model.encode(text).tolist()

    def get_embedding(self, text: str):
        """Public API for generating embeddings with caching."""
        if not text:
            return None
        try:
            return self._get_cached_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding for text: {e}")
            return None

embedding_service = EmbeddingService()
