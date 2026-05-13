import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from orchestrator.orchestrator import friday_orchestrator

async def run_identity_tests():
    """Automated tests for F.R.I.D.A.Y. identity and cognitive consistency."""
    test_prompts = [
        ("What is your name?", "Friday"),
        ("Who created you?", "Advanced Agentic Coding"),
        ("What company made you?", "Advanced Agentic Coding"),
        ("Are you ChatGPT?", "No"),
        ("Remember my favorite color is blue.", "Got it"),
        ("What is my favorite color?", "blue"),
        ("What year is it?", "2026"),
        ("Do you have memory?", "Yes")
    ]
    
    session_id = "test_identity_session"
    print(f"\n--- STARTING IDENTITY GOVERNANCE AUDIT ---\n")
    
    success_count = 0
    for prompt, expected_keyword in test_prompts:
        print(f"User: {prompt}")
        response = ""
        # Mock background tasks for test
        class MockTasks:
            def add_task(self, func, *args, **kwargs): pass
        
        async for token in friday_orchestrator.process_stream(session_id, prompt, "test_req", MockTasks()):
            if not token.startswith("[["):
                response += token
        
        print(f"Assistant: {response.strip()}")
        
        # Check for forbidden corporate references
        forbidden = ["Microsoft", "OpenAI", "Google", "platform policies", "as an AI"]
        has_forbidden = any(word.lower() in response.lower() for word in forbidden)
        
        # Check for identity keyword
        has_identity = expected_keyword.lower() in response.lower()
        
        if not has_forbidden and has_identity:
            print("Status: [PASS]")
            success_count += 1
        else:
            print(f"Status: [FAIL] (Forbidden: {has_forbidden}, Identity Match: {has_identity})")
        print("-" * 40)

    print(f"\nAudit Complete: {success_count}/{len(test_prompts)} passed.")

if __name__ == "__main__":
    # Add backend to path
    sys.path.append(os.getcwd())
    asyncio.run(run_identity_tests())
