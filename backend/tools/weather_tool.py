import os
import httpx
from tools.base_tool import BaseTool

class WeatherTool(BaseTool):
    name = "weather_lookup"
    description = "Get the current weather for a specific location."
    parameters = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City and country (e.g., 'London, UK')"}
        },
        "required": ["location"]
    }

    async def execute(self, location: str) -> str:
        # We can use wttr.in for a free, no-key weather lookup for production speed
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"https://wttr.in/{location}?format=j1")
                if response.status_code == 200:
                    data = response.json()
                    current = data['current_condition'][0]
                    temp = current['temp_C']
                    desc = current['weatherDesc'][0]['value']
                    humidity = current['humidity']
                    return f"Current weather in {location}: {temp}°C, {desc}. Humidity: {humidity}%."
                return f"Could not retrieve weather for {location}."
        except Exception as e:
            return f"Weather Error: {str(e)}"
