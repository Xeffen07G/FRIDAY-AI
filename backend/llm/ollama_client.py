import requests
import logging
import json
import time
from backend.config.settings import settings

logger = logging.getLogger("friday.llm")

class LLMClient:
    """Handles communication with local Ollama with automatic retries and strict error handling."""
    def __init__(self):
        self.model = settings.MODEL_NAME
        self.base_url = settings.OLLAMA_BASE_URL
        self.retry_count = settings.OLLAMA_RETRY_COUNT
        
    def generate_json(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", timeout: int = 5):
        """Sends a request to Ollama requesting strict JSON output with retry logic."""
        attempts = 0
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
                    
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "{}")
                
                logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed with status {response.status_code}")
                
            except (requests.exceptions.RequestException, Exception) as e:
                logger.warning(f"[REQ:{request_id}] JSON Attempt {attempts+1} failed: {e}")
            
            attempts += 1
            if attempts <= self.retry_count:
                time.sleep(0.5 * attempts)
                
        return "{}"

    def generate_stream(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", options: dict = None):
        """
        Sends a prompt to Ollama and streams the response back.
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
            
            with requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=settings.OLLAMA_TIMEOUT
            ) as response:
            
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                    return
                elif response.status_code == 404:
                    error_msg = f"Model '{self.model}' not found. Please run 'ollama pull {self.model}'."
                    logger.error(f"[REQ:{request_id}] {error_msg}")
                    yield error_msg
                else:
                    logger.error(f"[REQ:{request_id}] Ollama status {response.status_code}: {response.text}")
                    yield f"Error: LLM service returned status {response.status_code}."
                
        except requests.exceptions.ConnectionError:
            logger.error(f"[REQ:{request_id}] Failed to connect to Ollama at {self.base_url}")
            yield "❌ **Connection Error:** Ollama is not running. Please start Ollama to use F.R.I.D.A.Y."
        except Exception as e:
            logger.exception(f"[REQ:{request_id}] Unexpected LLM error: {e}")
            yield "❌ **LLM Error:** An unexpected error occurred while generating a response."
