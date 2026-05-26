import requests
import json
import uuid

def test_chat(message):
    # 1. Create session
    sess_url = "http://127.0.0.1:8000/api/sessions/"
    try:
        sess_resp = requests.post(sess_url, json={"title": "Test Chat"})
        sess_resp.raise_for_status()
        session_id = sess_resp.json()["id"]
    except Exception as e:
        print(f"Error creating session: {e}")
        return

    # 2. Chat
    url = "http://127.0.0.1:8000/api/chat/"
    nonce = str(uuid.uuid4())
    
    payload = {
        "session_id": session_id,
        "message": message,
        "nonce": nonce
    }
    
    print(f"\n--- Testing message: {message} ---")
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        full_text = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                print(chunk, end="", flush=True)
                full_text += chunk
        print("\n\n[Finished stream]")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat("hello")
    test_chat("tell me a joke")
    test_chat("describe the moon in 2 sentences")
