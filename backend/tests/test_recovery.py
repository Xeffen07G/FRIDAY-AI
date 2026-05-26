import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from memory.database import create_session, get_messages, delete_session, create_generation
from orchestrator.orchestrator import friday_orchestrator

class TestStreamRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_recovery_scenario(self):
        # 1. Create a session
        session = create_session("Recovery Test Session")
        session_id = session["id"]
        
        try:
            # 2. Simulate streaming with a mock client connection that disconnects
            request_id = "test_req_rec"
            nonce = "test_nonce_rec"
            user_input = "Hello, tell me a story."
            
            # Create the generation record in DB
            create_generation(nonce, session_id, nonce)
            
            # Call process_stream which yields chunks
            generator = friday_orchestrator.process_stream(
                session_id=session_id,
                user_input=user_input,
                request_id=request_id,
                nonce=nonce
            )
            
            # Consume 3 chunks and then simulate browser reload/disconnect by closing the generator
            chunks_received = []
            try:
                async for chunk in generator:
                    chunks_received.append(chunk)
                    if len(chunks_received) >= 3:
                        # Close the generator prematurely (browser refresh / tab disconnect)
                        await generator.aclose()
                        break
            except (GeneratorExit, asyncio.CancelledError):
                pass
                
            # 3. Trigger unified cancel path (as would be done by ws close / tab reload)
            await friday_orchestrator.cancel_generation(session_id)
            
            # 4. Reconnect & Hydrate: Fetch messages from the database
            messages = get_messages(session_id)
            
            # Verify the partial output is restored
            print(f"[TEST_DIAG] Retrieved messages: {messages}")
            self.assertTrue(len(messages) > 0)
            
        finally:
            # Cleanup
            delete_session(session_id)

if __name__ == '__main__':
    unittest.main()
