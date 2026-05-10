import requests
import logging
from backend.config.settings import settings

logger = logging.getLogger("friday.llm")

class LLMClient:
    """Handles communication with the local Ollama instance with robust error handling."""
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
                "format": "json"
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

    def generate_stream(self, prompt: str, system: str = None, request_id: str = "UNKNOWN"):
        """Sends a prompt to Ollama and streams the response back token by token."""
        try:
            logger.info(f"[REQ:{request_id}] Sending stream request to Ollama ({self.model})...")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True
            }
            if system:
                payload["system"] = system
                
            with requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=30 # Prevent hanging forever
            ) as response:
            
                # Handle standard successful response
                if response.status_code == 200:
                    import json
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                    return
                    
                # Handle specific Ollama errors
                elif response.status_code == 404:
                    error_msg = f"Model '{self.model}' not found in Ollama."
                    logger.error(f"[REQ:{request_id}] {error_msg}")
                    yield error_msg
                    return
                    
                elif response.status_code == 400:
                    logger.error(f"[REQ:{request_id}] Invalid request to Ollama: {response.text}")
                    yield "Error: Invalid request format sent to LLM."
                    return
                    
                else:
                    logger.error(f"[REQ:{request_id}] Ollama returned status {response.status_code}: {response.text}")
                    yield "Error: LLM encountered an unexpected issue."
                    return
                
        except requests.exceptions.ConnectionError:
            logger.error(f"[REQ:{request_id}] Failed to connect to Ollama at {self.base_url}")
            yield "Connection Error: Could not reach Ollama. Is the Ollama app running?"
            
        except requests.exceptions.Timeout:
            logger.error(f"[REQ:{request_id}] Ollama request timed out.")
            yield "Timeout Error: Ollama took too long to respond."
            
        except Exception as e:
            logger.exception(f"[REQ:{request_id}] Unexpected error in LLMClient stream.")
            yield "An unexpected error occurred while contacting the LLM."
