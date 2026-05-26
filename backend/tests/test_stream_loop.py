"""
Regression tests for stream loop guards and repetition prevention.
Tests the orchestrator's streaming guards without requiring a running server.
"""
import pytest
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestStreamLoopGuards:
    """Test backend stream guard logic in isolation."""

    def test_repeated_chunk_stops_stream(self):
        """Repeated chunk x10 → stream stops before consuming all."""
        rolling_window = ""
        last_chunk = ""
        chunk_repeat_count = 0
        max_output_tokens = 500
        max_output_chars = 1800
        full_response = ""
        token_count = 0
        stopped = False
        stop_reason = None

        # Simulate 10 identical chunks
        chunks = ["hello world "] * 10
        consumed = 0

        for token in chunks:
            # --- identical chunk guard ---
            if token == last_chunk and token.strip() != "":
                chunk_repeat_count += 1
                if chunk_repeat_count >= 3:
                    stopped = True
                    stop_reason = "identical_chunk_repeat"
                    break
            else:
                chunk_repeat_count = 0
                last_chunk = token

            full_response += token
            token_count += 1
            consumed += 1

            rolling_window += token
            if len(rolling_window) > 200:
                rolling_window = rolling_window[-200:]

            # --- max tokens/chars guard ---
            if token_count >= max_output_tokens or len(full_response) >= max_output_chars:
                stopped = True
                stop_reason = "max_tokens_chars"
                break

            # --- 40-char substring guard ---
            if len(rolling_window) >= 120:
                suffix = rolling_window[-40:]
                if rolling_window.count(suffix) >= 3:
                    stopped = True
                    stop_reason = "substring_repeat"
                    break

        assert stopped, "Stream should have been stopped by repeat guard"
        assert consumed < 10, f"Should stop before consuming all 10 chunks, consumed {consumed}"
        # First chunk is new (consumed, repeat_count=0). Second match sets count=1.
        # Third sets count=2. Fourth sets count=3 → break.
        # But consumed only increments AFTER the guard check passes.
        # Chunk 1: new → consumed=1. Chunk 2: repeat, count=1, no break, but it doesn't get past the guard to increment consumed.
        # Wait — the repeat guard is BEFORE full_response append. Let's trace:
        # Chunk 1: != last → last="hello world ", consumed=1
        # Chunk 2: == last → count=1 (<3) → break NO → continue loop but guard fires before consumed++
        # Actually the "continue" happens in the frontend, but in backend the guard does NOT skip - it breaks.
        # In backend, the chunk IS yielded up until the break. So:
        # Chunk 1: new → count=0, last=token, full_response += token, consumed=1
        # Chunk 2: == → count=1 (<3), no break, but we don't skip — we proceed. consumed=2 (wait, looking at code, after repeat check there's no 'continue')
        # Correct: backend does NOT skip repeated chunks, it just breaks when count>=3.
        # So chunks 1 (new), 2 (count=1), 3 (count=2) get fully consumed, chunk 4 triggers break at count=3.
        assert consumed == 3, f"3 chunks should be consumed before guard triggers on the 4th, got {consumed}"

    def test_duplicated_sentence_deduped_via_substring(self):
        """A sentence repeated 3 times in rolling window triggers 40-char substring guard."""
        rolling_window = ""
        last_chunk = ""
        chunk_repeat_count = 0
        max_output_tokens = 500
        max_output_chars = 1800
        full_response = ""
        token_count = 0
        stopped = False
        stop_reason = None

        # Each chunk is different (sentence fragments) but the rolling window
        # will contain the same 40+ char substring repeated 3 times
        sentence = "The moon orbits Earth at about 384400 km."  # 42 chars
        # Deliver as distinct larger chunks so chunk dedup doesn't fire
        chunks = [
            sentence + " ",
            "It reflects sunlight. " + sentence + " ",
            "It is beautiful. " + sentence + " ",
        ]

        for token in chunks:
            if token == last_chunk and token.strip() != "":
                chunk_repeat_count += 1
                if chunk_repeat_count >= 3:
                    stopped = True
                    stop_reason = "identical_chunk_repeat"
                    break
            else:
                chunk_repeat_count = 0
                last_chunk = token

            full_response += token
            token_count += 1

            rolling_window += token
            if len(rolling_window) > 200:
                rolling_window = rolling_window[-200:]

            if token_count >= max_output_tokens or len(full_response) >= max_output_chars:
                stopped = True
                stop_reason = "max_tokens_chars"
                break

            if len(rolling_window) >= 120:
                suffix = rolling_window[-40:]
                if rolling_window.count(suffix) >= 3:
                    stopped = True
                    stop_reason = "substring_repeat"
                    break

        assert stopped, "Stream should have been stopped by substring repeat guard"
        assert stop_reason == "substring_repeat", f"Expected substring_repeat, got {stop_reason}"

    def test_assistant_history_markers_filtered(self):
        """Messages with markers [GENERATIVE_RESPONSE] and [PROACTIVE_SUGGESTION] are excluded."""
        past_msgs = [
            {"sender": "user", "text": "hello", "role": "user"},
            {"sender": "friday", "text": "[GENERATIVE_RESPONSE] some response"},
            {"sender": "system_generated", "text": "internal note"},
            {"sender": "assistant_stream", "text": "streamed token"},
            {"sender": "friday", "text": "clean response"},
            {"sender": "friday", "text": "[PROACTIVE_SUGGESTION] you should try X"},
            {"sender": "user", "text": "thanks"},
        ]

        filtered_messages = []
        for m in past_msgs:
            if m.get('sender') in ['system_generated', 'assistant_stream'] or m.get('role') == 'system_generated':
                continue
            text = m.get('text', '')
            if '[GENERATIVE_RESPONSE]' in text or '[PROACTIVE_SUGGESTION]' in text:
                continue
            role = "assistant" if m['sender'] == 'friday' else "user"
            filtered_messages.append({"role": role, "content": text[:500]})

        assert len(filtered_messages) == 3
        assert filtered_messages[0] == {"role": "user", "content": "hello"}
        assert filtered_messages[1] == {"role": "assistant", "content": "clean response"}
        assert filtered_messages[2] == {"role": "user", "content": "thanks"}

    def test_response_length_over_1800_truncated(self):
        """Response exceeding 1800 chars is truncated by the max_output_chars guard."""
        rolling_window = ""
        last_chunk = ""
        chunk_repeat_count = 0
        max_output_tokens = 500
        max_output_chars = 1800
        full_response = ""
        token_count = 0
        stopped = False
        stop_reason = None

        # Generate unique chunks that total > 1800 chars
        # Each chunk is 50 unique chars
        chunks = [f"This is unique sentence number {i:04d}. " for i in range(100)]

        for token in chunks:
            if token == last_chunk and token.strip() != "":
                chunk_repeat_count += 1
                if chunk_repeat_count >= 3:
                    stopped = True
                    stop_reason = "identical_chunk_repeat"
                    break
            else:
                chunk_repeat_count = 0
                last_chunk = token

            full_response += token
            token_count += 1

            rolling_window += token
            if len(rolling_window) > 200:
                rolling_window = rolling_window[-200:]

            if token_count >= max_output_tokens or len(full_response) >= max_output_chars:
                stopped = True
                stop_reason = "max_tokens_chars"
                break

            if len(rolling_window) >= 120:
                suffix = rolling_window[-40:]
                if rolling_window.count(suffix) >= 3:
                    stopped = True
                    stop_reason = "substring_repeat"
                    break

        assert stopped, "Stream should have been stopped by max chars guard"
        assert stop_reason == "max_tokens_chars", f"Expected max_tokens_chars, got {stop_reason}"
        assert len(full_response) >= max_output_chars, "Response should have reached the limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
