import requests
import json
import uuid
import base64
import re
import sys

BASE = "http://127.0.0.1:8000"

def decode_stream(raw_text):
    """Extract and decode all [[TOKEN:...]] from raw stream text."""
    tokens = re.findall(r'\[\[TOKEN:[^]]+\]\]', raw_text)
    decoded = ""
    for t in tokens:
        inner = t[8:-2]  # strip [[TOKEN: and ]]
        parts = inner.split(":")
        b64 = ":".join(parts[3:])  # everything after session:msg:gen
        try:
            decoded += base64.b64decode(b64).decode("utf-8")
        except Exception:
            pass
    return decoded

def test_chat(message):
    # Create session
    try:
        sess_resp = requests.post(f"{BASE}/api/sessions/", json={"title": "Test"})
        sess_resp.raise_for_status()
        session_id = sess_resp.json()["id"]
    except Exception as e:
        print(f"  ERROR creating session: {e}")
        return None

    nonce = str(uuid.uuid4())
    payload = {"session_id": session_id, "message": message, "nonce": nonce}

    print(f"\n{'='*60}")
    print(f"PROMPT: {message}")
    print(f"{'='*60}")

    try:
        resp = requests.post(f"{BASE}/api/chat/", json=payload, stream=True, timeout=120)
        resp.raise_for_status()

        raw = ""
        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                raw += chunk

        # Decode tokens
        decoded_text = decode_stream(raw)
        if not decoded_text:
            # Fallback: strip control tokens for deterministic responses
            cleaned = raw
            cleaned = re.sub(r'\[\[STATUS:[^\]]*\]\]', '', cleaned)
            cleaned = re.sub(r'\[\[METRICS:[^\]]*\]\]', '', cleaned)
            cleaned = re.sub(r'\[GENERATIVE_RESPONSE\]\s*', '', cleaned)
            cleaned = re.sub(r'\[DETERMINISTIC_RESPONSE\]\s*', '', cleaned)
            decoded_text = cleaned.strip()

        # Extract metrics
        metrics_match = re.search(r'\[\[METRICS:(\{[^}]+\})\]\]', raw)
        metrics = json.loads(metrics_match.group(1)) if metrics_match else {}

        print(f"\nRESPONSE TEXT:")
        print(f"  {decoded_text}")
        print(f"\nMETRICS:")
        print(f"  token_count: {metrics.get('token_count', 'N/A')}")
        print(f"  total_ms: {metrics.get('total_ms', 'N/A')}")
        print(f"  execution_mode: {metrics.get('execution_mode', 'N/A')}")
        print(f"  char_count: {len(decoded_text)}")

        # VALIDATION
        print(f"\nVALIDATION:")
        passed = True

        # Check: no duplicated phrase (any 10+ char substring appearing 2+ times)
        dup_found = False
        text_lower = decoded_text.lower()
        for length in range(15, len(text_lower)//2 + 1):
            for i in range(len(text_lower) - length):
                substr = text_lower[i:i+length]
                if text_lower.count(substr) >= 2:
                    dup_found = True
                    print(f"  [FAIL] Duplicated phrase found: '{substr[:50]}...'")
                    break
            if dup_found:
                break
        if not dup_found:
            print(f"  [PASS] No duplicated phrases")

        # Check: total response < 1800 chars
        if len(decoded_text) < 1800:
            print(f"  [PASS] Response length {len(decoded_text)} < 1800 chars")
        else:
            print(f"  [FAIL] Response length {len(decoded_text)} >= 1800 chars")
            passed = False

        # Check: output stops naturally (stream finished)
        if "[[METRICS:" in raw:
            print(f"  [PASS] Stream completed naturally (METRICS received)")
        else:
            print(f"  [FAIL] Stream did not complete (no METRICS)")
            passed = False

        return passed
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    prompts = ["hello", "tell me a joke", "describe the moon in 2 sentences"]
    results = {}
    
    for p in prompts:
        results[p] = test_chat(p)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    all_pass = True
    for p, r in results.items():
        status = "PASS" if r else "FAIL"
        if not r:
            all_pass = False
        print(f"  [{status}] {p}")
    
    print(f"\nOVERALL: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
