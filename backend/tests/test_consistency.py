import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
import sqlite3
from datetime import datetime
from memory.database import (
    create_session,
    delete_session,
    create_generation,
    update_generation_state,
    get_generation_state,
    get_connection,
    save_message
)
from orchestrator.orchestrator import friday_orchestrator

class TestGenerationConsistency(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        session = create_session("Consistency Test Session")
        self.session_id = session["id"]

    def tearDown(self):
        delete_session(self.session_id)
        # Clear test generations
        conn = get_connection()
        try:
            conn.cursor().execute("DELETE FROM generations WHERE session_id = ?", (self.session_id,))
            conn.commit()
        finally:
            conn.close()

    def test_exactly_once_completion_and_locks(self):
        """Assert exactly-once state transitions and terminal state locking."""
        generation_id = "test_gen_1"
        create_generation(generation_id, self.session_id, "req_1")
        
        # Initial state should be CREATED
        self.assertEqual(get_generation_state(generation_id), "CREATED")
        
        # Valid transition: CREATED -> STREAMING is not allowed directly under completed rule, wait
        # Let's check update_generation_state rules:
        # STREAMING -> COMPLETED is allowed exactly once.
        # Transitions from final states CANCELLED and COMPLETED are blocked.
        
        # Let's update state to STREAMING
        success = update_generation_state(generation_id, "STREAMING")
        self.assertTrue(success)
        self.assertEqual(get_generation_state(generation_id), "STREAMING")
        
        # First completion: STREAMING -> COMPLETED should succeed
        success = update_generation_state(generation_id, "COMPLETED")
        self.assertTrue(success)
        self.assertEqual(get_generation_state(generation_id), "COMPLETED")
        
        # Try second completion or hijacking transition: COMPLETED -> STREAMING should fail
        success = update_generation_state(generation_id, "STREAMING")
        self.assertFalse(success)
        self.assertEqual(get_generation_state(generation_id), "COMPLETED") # remains COMPLETED
        
        # Transitioning COMPLETED -> COMPLETED should fail because current_state is not STREAMING
        success = update_generation_state(generation_id, "COMPLETED")
        self.assertFalse(success)

    def test_adversarial_cancel(self):
        """Verify that a cancelled generation rejects future DB writes and halts streams."""
        generation_id = "test_gen_cancel"
        create_generation(generation_id, self.session_id, "req_cancel")
        
        # Transition to STREAMING
        update_generation_state(generation_id, "STREAMING")
        
        # Cancel the generation
        update_generation_state(generation_id, "CANCELLED")
        self.assertEqual(get_generation_state(generation_id), "CANCELLED")
        
        # Attempt to save a message under the cancelled client_request_id/nonce
        # save_message should return CANCELLED
        res = save_message(
            session_id=self.session_id,
            role="friday",
            content="This should not be saved",
            client_request_id=generation_id
        )
        self.assertEqual(res, "CANCELLED")

    def test_duplicate_db_protection(self):
        """Assert identical client_request_ids/nonces trigger UNIQUE index conflict on messages."""
        nonce = "test_dup_nonce"
        
        # Save first message with nonce
        res1 = save_message(
            session_id=self.session_id,
            role="user",
            content="First send",
            request_nonce=nonce
        )
        self.assertNotEqual(res1, "DUPLICATE")
        self.assertNotEqual(res1, "CANCELLED")
        
        # Save second message with duplicate nonce should return DUPLICATE
        res2 = save_message(
            session_id=self.session_id,
            role="user",
            content="Second send",
            request_nonce=nonce
        )
        self.assertEqual(res2, "DUPLICATE")

    async def test_shutdown_cleanup_simulation(self):
        """Simulate backend shutdown database hook that cancels active generations."""
        generation_id_active = "test_gen_shutdown_active"
        generation_id_done = "test_gen_shutdown_done"
        
        create_generation(generation_id_active, self.session_id, "req_shut_1")
        create_generation(generation_id_done, self.session_id, "req_shut_2")
        
        update_generation_state(generation_id_active, "STREAMING")
        update_generation_state(generation_id_done, "STREAMING")
        update_generation_state(generation_id_done, "COMPLETED")
        
        # Run shutdown database query simulation
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE generations SET state = 'CANCELLED', updated_at = ? WHERE state IN ('CREATED', 'ACCEPTED', 'STREAMING')",
                (datetime.now().isoformat(),)
            )
            conn.commit()
        finally:
            conn.close()
            
        # The active generation should now be CANCELLED
        self.assertEqual(get_generation_state(generation_id_active), "CANCELLED")
        # The completed generation should remain COMPLETED
        self.assertEqual(get_generation_state(generation_id_done), "COMPLETED")

if __name__ == '__main__':
    unittest.main()
