import requests
import logging
import json
import time
from backend.config.settings import settings

logger = logging.getLogger("friday.llm")

class LLMClient:
    """Handles communication with the local Ollama instance with robust error handling and speed optimizations."""
    def __init__(self):
        self.model = settings.MODEL_NAME
        self.base_url = settings.OLLAMA_BASE_URL
        
    def generate_json(self, prompt: str, system: str = None, request_id: str = "UNKNOWN"):
        """Sends a request to Ollama requesting strict JSON output."""
        try:
            logger.info(f"[REQ:{request_id}] Sending JSON tool routing request to Ollama ({self.model})...")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "num_predict": 128 # Routing should be short
                }
            }
            if system:
                payload["system"] = system
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "{}")
                
            logger.error(f"[REQ:{request_id}] JSON Generation HTTP Error: {response.status_code}")
            return "{}"
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Error in JSON generation: {e}")
            return "{}"

    def generate_stream(self, prompt: str, system: str = None, request_id: str = "UNKNOWN", options: dict = None):
        """
        Sends a prompt to Ollama and streams the response back token by token.
        Supports dynamic generation options for latency optimization.
        """
        try:
            logger.info(f"[REQ:{request_id}] Sending stream request to Ollama ({self.model})...")
            
            # Default optimized options for local inference
            final_options = {
                "temperature": 0.7,
                "num_predict": 512,
                "stop": ["User:", "Assistant:"]
            }
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
                
            first_token_time = None
            start_time = time.time()
            
            with requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=30
            ) as response:
            
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                if first_token_time is None:
                                    first_token_time = time.time() - start_time
                                    logger.info(f"[REQ:{request_id}] First token in {first_token_time*1000:.1f}ms")
                                yield data["response"]
                    return
                    
                else:
                    logger.error(f"[REQ:{request_id}] Ollama returned status {response.status_code}: {response.text}")
                    yield "Error: LLM encountered an unexpected issue."
                    return
                
        except requests.exceptions.ConnectionError:
            logger.error(f"[REQ:{request_id}] Failed to connect to Ollama")
            yield "Connection Error: Could not reach Ollama."
            
        except Exception as e:
            logger.exception(f"[REQ:{request_id}] Unexpected error in LLMClient stream.")
            yield "An unexpected error occurred while contacting the LLM."
