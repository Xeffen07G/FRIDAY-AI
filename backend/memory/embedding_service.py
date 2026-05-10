import logging
from sentence_transformers import SentenceTransformer
import os

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
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}", exc_info=True)
                raise

    def get_embedding(self, text: str):
        if not self.initialized:
            try:
                self._initialize()
            except Exception:
                return None
        
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

embedding_service = EmbeddingService()
