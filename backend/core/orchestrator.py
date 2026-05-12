from tools.router import ToolRouter
from core.llm import LLMClient

class Orchestrator:
    def __init__(self):
        self.tool_router = ToolRouter()
        self.llm = LLMClient(model="qwen2.5")
    
    async def process(self, user_input: str) -> str:
        # Step 1: Detect intent via LLM or basic parsing
        intent_response = self.llm.generate(f"Determine the primary tool needed for this request. Available tools: {self.tool_router.get_available_tools()}. Request: {user_input}")
        
        # Step 2: Route to tool if necessary
        tool_result = await self.tool_router.route(intent_response, user_input)
        
        if tool_result:
            return tool_result
            
        # Step 3: Default to conversational LLM response
        return self.llm.generate(user_input)
