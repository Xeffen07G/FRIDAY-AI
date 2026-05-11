import httpx
import time
from typing import List, Optional
from backend.config.settings import settings
from backend.core.logger import get_logger

logger = get_logger("core.model_manager")

class ModelManager:
    """Manages Ollama model lifecycle (loading/unloading/health)."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self._last_used = {}
        self._active_models = []

    async def get_active_models(self) -> List[str]:
        """Fetches currently loaded models from Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                # Ollama /api/ps shows loaded models
                response = await client.get(f"{self.base_url}/api/ps")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    self._active_models = models
                    return models
        except Exception as e:
            logger.error(f"Failed to fetch active models: {e}")
        return []

    async def unload_model(self, model_name: str) -> bool:
        """Unloads a model from GPU/RAM by sending an empty keep_alive."""
        try:
            logger.info(f"Requesting unload for model: {model_name}")
            async with httpx.AsyncClient() as client:
                # Sending keep_alive="0" unloads the model
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model_name, "keep_alive": 0},
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to unload model {model_name}: {e}")
            return False

    async def ensure_model(self, model_name: str) -> bool:
        """Checks if model is loaded, updates usage timestamp."""
        self._last_used[model_name] = time.time()
        active = await self.get_active_models()
        return any(model_name in m for m in active)

    async def cleanup_inactive_models(self, idle_seconds: int = 300):
        """Unloads models that haven't been used for a while."""
        now = time.time()
        active = await self.get_active_models()
        
        for model in active:
            last_used = self._last_used.get(model, 0)
            if now - last_used > idle_seconds:
                logger.info(f"Model {model} is idle. Unloading to save RAM.")
                await self.unload_model(model)

    def is_ram_under_pressure(self, threshold_percent: float = 85.0) -> bool:
        """Checks if system RAM usage is above the threshold."""
        try:
            import psutil
            return psutil.virtual_memory().percent > threshold_percent
        except:
            return False

    def get_diagnostics(self):
        return {
            "active_models": self._active_models,
            "last_used": {k: time.strftime("%H:%M:%S", time.localtime(v)) for k, v in self._last_used.items()}
        }

model_manager = ModelManager()
