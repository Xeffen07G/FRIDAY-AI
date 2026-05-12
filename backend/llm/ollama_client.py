import httpx
import json
import asyncio
from config.settings import settings
from core.logger import get_logger

logger = get_logger("llm")

class LLMClient:
    """Handles async communication with local Ollama with automatic retries and strict error handling."""
    def __init__(self):
        self.model = settings.MODEL_NAME
        self.base_url = settings.OLLAMA_BASE_URL
        self.retry_count = settings.OLLAMA_RETRY_COUNT
        self.timeout = settings.OLLAMA_TIMEOUT
        
    async def generate_json(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", timeout: int = 5, retries: int = None):
        """Sends an async request to Ollama requesting strict JSON output."""
        max_attempts = retries if retries is not None else self.retry_count
        attempts = 0
        async with httpx.AsyncClient(timeout=timeout) as client:
            while attempts <= max_attempts:
                try:
                    payload = {
                        "model": self.model,
                        "messages": [],
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.0, 
                            "num_predict": 128,
                            "num_thread": 8,
                            "num_ctx": 2048,
                            "repeat_penalty": 1.1
                        }
                    }
                    if system:
                        payload["messages"].append({"role": "system", "content": system})
                    payload["messages"].append({"role": "user", "content": prompt})
                        
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        return response.json().get("message", {}).get("content", "{}")
                    
                    logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed with status {response.status_code}")
                    
                except (httpx.RequestError, Exception) as e:
                    logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed: {e}")
                
                attempts += 1
                if attempts <= self.retry_count:
                    await asyncio.sleep(0.5 * attempts)
                    
            return "{}"

    async def generate_stream(self, messages: list, options: dict = None, request_id: str = "UNKNOWN"):
        """
        Sends an array of messages to Ollama's Chat API and streams the response back.
        Using native message arrays prevents prompt leakage and improves instruction following.
        """
        try:
            final_options = {
                "temperature": 0.7, 
                "num_predict": 256, 
                "stop": ["User:", "Assistant:"],
                "num_thread": 8,
                "num_ctx": 4096,
                "repeat_penalty": 1.2,
                "top_k": 20,
                "top_p": 0.9
            }
            if options:
                final_options.update(options)

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": final_options
            }
                
            logger.info(f"[REQ:{request_id}] Initiating Ollama Chat stream for model: {self.model}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
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
