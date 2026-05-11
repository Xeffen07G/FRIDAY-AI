import httpx
import json
import asyncio
from backend.config.settings import settings
from backend.core.logger import get_logger

logger = get_logger("llm")

class LLMClient:
    """Handles async communication with local Ollama with automatic retries and strict error handling."""
    def __init__(self):
        self.model = settings.MODEL_NAME
        self.base_url = settings.OLLAMA_BASE_URL
        self.retry_count = settings.OLLAMA_RETRY_COUNT
        self.timeout = settings.OLLAMA_TIMEOUT
        
    async def generate_json(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", timeout: int = 5):
        """Sends an async request to Ollama requesting strict JSON output with retry logic."""
        attempts = 0
        async with httpx.AsyncClient(timeout=timeout) as client:
            while attempts <= self.retry_count:
                try:
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.0, "num_predict": 128}
                    }
                    if system:
                        payload["system"] = system
                        
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        return response.json().get("response", "{}")
                    
                    logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed with status {response.status_code}")
                    
                except (httpx.RequestError, Exception) as e:
                    logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed: {e}")
                
                attempts += 1
                if attempts <= self.retry_count:
                    await asyncio.sleep(0.5 * attempts)
                    
            return "{}"

    async def generate_stream(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", options: dict = None):
        """
        Sends a prompt to Ollama and streams the response back asynchronously.
        Includes graceful fallback if Ollama is unreachable.
        """
        try:
            final_options = {"temperature": 0.7, "num_predict": 512, "stop": ["User:", "Assistant:"]}
            if options:
                final_options.update(options)
                
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": final_options
            }
            if system:
                payload["system"] = system
                
            logger.info(f"[REQ:{request_id}] Initiating Ollama stream for model: {self.model}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done"):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    elif response.status_code == 404:
                        error_msg = f"Model '{self.model}' not found. Please run 'ollama pull {self.model}'."
                        logger.error(f"[REQ:{request_id}] {error_msg}")
                        yield error_msg
                    else:
                        logger.error(f"[REQ:{request_id}] Ollama status {response.status_code}: {response.text}")
                        yield f"Error: LLM service returned status {response.status_code}."
                    
        except httpx.ConnectError:
            logger.error(f"[REQ:{request_id}] Failed to connect to Ollama at {self.base_url}")
            yield "❌ **Connection Error:** Ollama is not running. Please start Ollama to use F.R.I.D.A.Y."
        except Exception as e:
            logger.exception(f"[REQ:{request_id}] Unexpected LLM error: {e}")
            yield "❌ **LLM Error:** An unexpected error occurred while generating a response."
