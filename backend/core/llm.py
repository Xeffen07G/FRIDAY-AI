import subprocess
import requests

class LLMClient:
    def __init__(self, model="qwen2.5", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"LLM Error: {response.text}"
        except Exception as e:
            return f"Could not connect to Ollama: {str(e)}"
