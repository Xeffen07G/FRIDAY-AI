import os
import httpx
import logging
from tools.base_tool import BaseTool

logger = logging.getLogger("friday.tools.web_search")

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet for news, current events, and realtime information. Mandatory for 'latest' or 'today' queries."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query (e.g., 'latest tech news')"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str) -> str:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "ERROR: Tavily API key not found. I cannot search the live web without a valid key in the .env file."

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "search_depth": "smart",
                        "include_answer": True,
                        "max_results": 3
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    formatted = []
                    for r in results:
                        formatted.append(f"Source: {r.get('url')}\nContent: {r.get('content')[:500]}...")
                    
                    return "\n\n".join(formatted) if formatted else "No results found."
                return f"Error: Tavily API returned status {response.status_code}"
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Search Error: {str(e)}"
