import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from memory.database import create_session, delete_session, create_generation
from memory.vector_store import vector_store
from orchestrator.orchestrator import friday_orchestrator

class TestMemoryRecallHardening(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        session = create_session("Memory Test Session")
        self.session_id = session["id"]
        try:
            all_m = vector_store.get_all_memories()
            for m in all_m:
                vector_store.delete_memory(m["id"])
        except Exception as e:
            pass

    def tearDown(self):
        delete_session(self.session_id)
        try:
            all_m = vector_store.get_all_memories()
            for m in all_m:
                vector_store.delete_memory(m["id"])
        except Exception as e:
            pass

    async def test_01_store_and_recall_color(self):
        """User: my favorite color is blue -> User: what is my favorite color -> Blue."""
        # 1. Store color
        nonce_store = "store_color_nonce"
        create_generation(nonce_store, self.session_id, nonce_store)
        store_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my favorite color is blue",
            request_id="store_color_req",
            nonce=nonce_store
        )
        async for chunk in store_generator: pass

        # 2. Recall color
        nonce_recall = "recall_color_nonce"
        create_generation(nonce_recall, self.session_id, nonce_recall)
        recall_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="what is my favorite color",
            request_id="recall_color_req",
            nonce=nonce_recall
        )
        recall_res = []
        async for chunk in recall_generator:
            recall_res.append(chunk)
            
        import base64
        found_token = False
        decoded_text = ""
        for chunk in recall_res:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                b64_val = parts[-1]
                decoded_text += base64.b64decode(b64_val).decode('utf-8')
                found_token = True
                
        self.assertTrue(found_token)
        self.assertEqual(decoded_text.strip(), "Blue.")

    async def test_02_store_and_recall_name(self):
        """User: remember sayak is my name -> User: what is my name -> sayak."""
        # 1. Store name
        nonce_store = "store_name_nonce"
        create_generation(nonce_store, self.session_id, nonce_store)
        store_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="remember sayak is my name",
            request_id="store_name_req",
            nonce=nonce_store
        )
        async for chunk in store_generator: pass

        # 2. Recall name
        nonce_recall = "recall_name_nonce"
        create_generation(nonce_recall, self.session_id, nonce_recall)
        recall_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="what is my name",
            request_id="recall_name_req",
            nonce=nonce_recall
        )
        recall_res = []
        async for chunk in recall_generator:
            recall_res.append(chunk)
            
        import base64
        found_token = False
        decoded_text = ""
        for chunk in recall_res:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                b64_val = parts[-1]
                decoded_text += base64.b64decode(b64_val).decode('utf-8')
                found_token = True
                
        self.assertTrue(found_token)
        self.assertEqual(decoded_text.strip(), "sayak")

    async def test_03_unknown_dog_name(self):
        """User: what is my dog name -> I don't know."""
        nonce_recall = "recall_dog_nonce"
        create_generation(nonce_recall, self.session_id, nonce_recall)
        recall_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="what is my dog name",
            request_id="recall_dog_req",
            nonce=nonce_recall
        )
        recall_res = []
        async for chunk in recall_generator:
            recall_res.append(chunk)
            
        import base64
        decoded_text = ""
        for chunk in recall_res:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                b64_val = parts[-1]
                decoded_text += base64.b64decode(b64_val).decode('utf-8')
                
        self.assertEqual(decoded_text.strip(), "I don't know.")

    async def test_04_unknown_generic(self):
        """User: what is my phone number -> I don't know."""
        nonce_recall = "recall_phone_nonce"
        create_generation(nonce_recall, self.session_id, nonce_recall)
        recall_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="what is my phone number",
            request_id="recall_phone_req",
            nonce=nonce_recall
        )
        recall_res = []
        async for chunk in recall_generator:
            recall_res.append(chunk)
            
        import base64
        decoded_text = ""
        for chunk in recall_res:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                b64_val = parts[-1]
                decoded_text += base64.b64decode(b64_val).decode('utf-8')
                
        self.assertEqual(decoded_text.strip(), "I don't know.")

    async def test_05_persona_isolation_and_forbidden_terms(self):
        """Verify memory recall bypasses assistant system prompt identity and blocks forbidden terms."""
        # 1. Store a memory containing forbidden terms like "premium" and "operating layer"
        nonce_store = "store_forbidden_nonce"
        create_generation(nonce_store, self.session_id, nonce_store)
        store_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my favorite color is premium blue on the operating layer",
            request_id="store_forbidden_req",
            nonce=nonce_store
        )
        async for chunk in store_generator: pass

        # 2. Recall color
        nonce_recall = "recall_forbidden_nonce"
        create_generation(nonce_recall, self.session_id, nonce_recall)
        recall_generator = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="what is my favorite color",
            request_id="recall_forbidden_req",
            nonce=nonce_recall
        )
        recall_res = []
        async for chunk in recall_generator:
            recall_res.append(chunk)
            
        import base64
        decoded_text = ""
        for chunk in recall_res:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                b64_val = parts[-1]
                decoded_text += base64.b64decode(b64_val).decode('utf-8')
                
        self.assertNotIn("premium", decoded_text.lower())
        self.assertNotIn("operating layer", decoded_text.lower())

    async def test_06_bulk_rapid_session_switching_and_20_recalls(self):
        """Verify correctness of 20 rapid sequential recall/storage tests."""
        for i in range(10):
            store_nonce = f"bulk_store_nonce_{i}"
            create_generation(store_nonce, self.session_id, store_nonce)
            store_generator = friday_orchestrator.process_stream(
                session_id=self.session_id,
                user_input=f"my favorite color is color{i}",
                request_id=f"bulk_store_req_{i}",
                nonce=store_nonce
            )
            async for chunk in store_generator: pass
            
            recall_nonce = f"bulk_recall_nonce_{i}"
            create_generation(recall_nonce, self.session_id, recall_nonce)
            recall_generator = friday_orchestrator.process_stream(
                session_id=self.session_id,
                user_input="what is my favorite color",
                request_id=f"bulk_recall_req_{i}",
                nonce=recall_nonce
            )
            recall_res = []
            async for chunk in recall_generator:
                recall_res.append(chunk)
                
            import base64
            decoded_text = ""
            for chunk in recall_res:
                if "[[TOKEN:" in chunk:
                    parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                    b64_val = parts[-1]
                    decoded_text += base64.b64decode(b64_val).decode('utf-8')
            
            expected = f"Color{i}."
            self.assertEqual(decoded_text.strip(), expected)

    async def test_07_new_golden_cases(self):
        """Verify new required recall cases: dog name = max, favorite color = red, name = sayak."""
        # 1. Store: my dog name is max
        nonce_store1 = "store_dog_max"
        create_generation(nonce_store1, self.session_id, nonce_store1)
        store_gen1 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my dog name is max",
            request_id="store_dog_max_req",
            nonce=nonce_store1
        )
        async for chunk in store_gen1: pass

        # Recall: whats my dog name
        nonce_recall1 = "recall_dog_max"
        create_generation(nonce_recall1, self.session_id, nonce_recall1)
        recall_gen1 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="whats my dog name",
            request_id="recall_dog_max_req",
            nonce=nonce_recall1
        )
        res1 = []
        async for chunk in recall_gen1: res1.append(chunk)
        
        # Decode res1
        import base64
        text1 = ""
        for chunk in res1:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                text1 += base64.b64decode(parts[-1]).decode('utf-8')
        self.assertEqual(text1.strip(), "Max.")

        # 2. Store: my favorite color is red
        nonce_store2 = "store_color_red"
        create_generation(nonce_store2, self.session_id, nonce_store2)
        store_gen2 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my favorite color is red",
            request_id="store_color_red_req",
            nonce=nonce_store2
        )
        async for chunk in store_gen2: pass

        # Recall: tell me my favorite color
        nonce_recall2 = "recall_color_red"
        create_generation(nonce_recall2, self.session_id, nonce_recall2)
        recall_gen2 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="tell me my favorite color",
            request_id="recall_color_red_req",
            nonce=nonce_recall2
        )
        res2 = []
        async for chunk in recall_gen2: res2.append(chunk)
        
        # Decode res2
        text2 = ""
        for chunk in res2:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                text2 += base64.b64decode(parts[-1]).decode('utf-8')
        self.assertEqual(text2.strip(), "Red.")

        # 3. Store: remember my name is sayak
        nonce_store3 = "store_name_sayak"
        create_generation(nonce_store3, self.session_id, nonce_store3)
        store_gen3 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="remember my name is sayak",
            request_id="store_name_sayak_req",
            nonce=nonce_store3
        )
        async for chunk in store_gen3: pass

        # Recall: do you know my name
        nonce_recall3 = "recall_name_sayak"
        create_generation(nonce_recall3, self.session_id, nonce_recall3)
        recall_gen3 = friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="do you know my name",
            request_id="recall_name_sayak_req",
            nonce=nonce_recall3
        )
        res3 = []
        async for chunk in recall_gen3: res3.append(chunk)
        
        # Decode res3
        text3 = ""
        for chunk in res3:
            if "[[TOKEN:" in chunk:
                parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                text3 += base64.b64decode(parts[-1]).decode('utf-8')
        self.assertEqual(text3.strip(), "sayak")

    async def test_08_cross_session_profile_persistence_and_isolated_conversation(self):
        """Verify profile scope is cross-session, but conversation scope is session-isolated."""
        # 1. Chat A (self.session_id) stores profile and conversation facts
        nonce_store_prof = "store_prof_a"
        create_generation(nonce_store_prof, self.session_id, nonce_store_prof)
        async for chunk in friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my favorite color is blue",
            request_id="store_prof_a_req",
            nonce=nonce_store_prof
        ): pass

        nonce_store_conv = "store_conv_a"
        create_generation(nonce_store_conv, self.session_id, nonce_store_conv)
        async for chunk in friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my current bug is websocket",
            request_id="store_conv_a_req",
            nonce=nonce_store_conv
        ): pass

        # 2. Chat B (new clean session ID) queries both
        session_b = create_session("Session B")
        session_b_id = session_b["id"]
        try:
            # Query Profile Color in Chat B
            nonce_recall_prof = "recall_prof_b"
            create_generation(nonce_recall_prof, session_b_id, nonce_recall_prof)
            res_prof = []
            async for chunk in friday_orchestrator.process_stream(
                session_id=session_b_id,
                user_input="what is my favorite color",
                request_id="recall_prof_b_req",
                nonce=nonce_recall_prof
            ):
                res_prof.append(chunk)

            # Decode color
            import base64
            color_text = ""
            for chunk in res_prof:
                if "[[TOKEN:" in chunk:
                    parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                    color_text += base64.b64decode(parts[-1]).decode('utf-8')
            self.assertEqual(color_text.strip(), "Blue.")

            # Query Conversation Bug in Chat B (should be I don't know.)
            nonce_recall_conv = "recall_conv_b"
            create_generation(nonce_recall_conv, session_b_id, nonce_recall_conv)
            res_conv = []
            async for chunk in friday_orchestrator.process_stream(
                session_id=session_b_id,
                user_input="what is my current bug",
                request_id="recall_conv_b_req",
                nonce=nonce_recall_conv
            ):
                res_conv.append(chunk)

            # Decode bug
            bug_text = ""
            for chunk in res_conv:
                if "[[TOKEN:" in chunk:
                    parts = chunk.replace("[[TOKEN:", "").replace("]]", "").split(":")
                    bug_text += base64.b64decode(parts[-1]).decode('utf-8')
            self.assertEqual(bug_text.strip(), "I don't know.")
        finally:
            delete_session(session_b_id)

    async def test_09_user_isolation_safeguard(self):
        """Verify profile matches are strictly filtered by user_id to prevent cross-user contamination."""
        # 1. Store favorite color for default_user
        nonce_store = "store_user_a"
        create_generation(nonce_store, self.session_id, nonce_store)
        async for chunk in friday_orchestrator.process_stream(
            session_id=self.session_id,
            user_input="my favorite color is blue",
            request_id="store_user_a_req",
            nonce=nonce_store
        ): pass

        # 2. Query as a different user using profile_lookup directly
        from orchestrator.orchestrator import profile_lookup
        ans_default = profile_lookup("default_user", "favorite_color")
        ans_other = profile_lookup("other_user", "favorite_color")
        
        self.assertEqual(ans_default, "Blue.")
        self.assertIsNone(ans_other)

if __name__ == '__main__':
    unittest.main()
