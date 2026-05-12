import asyncio
import websockets
import json
import base64

# Generate dummy 16kHz WAV data for testing
def generate_wav(duration_sec, freq=440):
    import struct
    import math
    sample_rate = 16000
    num_samples = int(duration_sec * sample_rate)
    
    # WAV header
    header = b'RIFF'
    header += struct.pack('<I', 36 + num_samples * 2)
    header += b'WAVEfmt '
    header += struct.pack('<I', 16) # Subchunk1Size
    header += struct.pack('<H', 1)  # AudioFormat (PCM)
    header += struct.pack('<H', 1)  # NumChannels
    header += struct.pack('<I', sample_rate) # SampleRate
    header += struct.pack('<I', sample_rate * 2) # ByteRate
    header += struct.pack('<H', 2)  # BlockAlign
    header += struct.pack('<H', 16) # BitsPerSample
    header += b'data'
    header += struct.pack('<I', num_samples * 2)
    
    # Audio data
    data = bytearray()
    for i in range(num_samples):
        # generate sine wave
        val = int(32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
        data.extend(struct.pack('<h', val))
        
    return header + data

async def test_websocket():
    uri = "ws://127.0.0.1:8001/api/ws/voice"
    
    # Test 1: Tiny payload (should be rejected/idle immediately)
    print("\n--- TEST 1: Tiny Payload (100ms) ---")
    async with websockets.connect(uri) as ws:
        wav_data = generate_wav(0.1)
        b64 = base64.b64encode(wav_data).decode('utf-8')
        await ws.send(json.dumps({"type": "audio_final", "data": b64, "session_id": "t1"}))
        try:
            res = await asyncio.wait_for(ws.recv(), 3.0)
            print(f"Received: {res}")
            res2 = await asyncio.wait_for(ws.recv(), 3.0)
            print(f"Received: {res2}")
        except asyncio.TimeoutError:
            print("Timeout (expected for tiny payload or idle returned)")

    # Test 2: Valid payload (should trigger STT, possibly generate some error or response)
    # Since it's a pure sine wave, STT might return empty, but it will process.
    print("\n--- TEST 2: Valid Payload (2.0s) ---")
    async with websockets.connect(uri) as ws:
        wav_data = generate_wav(2.0)
        b64 = base64.b64encode(wav_data).decode('utf-8')
        await ws.send(json.dumps({"type": "audio_final", "data": b64, "session_id": "t2"}))
        for _ in range(4):
            try:
                msg = await asyncio.wait_for(ws.recv(), 5.0)
                data = json.loads(msg)
                print(f"Received {data['type']}")
                if data['type'] == 'status' and data['data'] == 'idle': break
            except asyncio.TimeoutError:
                break
                
    # Test 3: Interruption
    print("\n--- TEST 3: Interruption ---")
    async with websockets.connect(uri) as ws:
        wav_data = generate_wav(1.0)
        b64 = base64.b64encode(wav_data).decode('utf-8')
        await ws.send(json.dumps({"type": "audio_final", "data": b64, "session_id": "t3"}))
        await asyncio.sleep(0.5) # let it start transcribing
        print("Sending interrupt...")
        await ws.send(json.dumps({"type": "interrupt"}))
        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), 2.0)
                print(f"Post-interrupt msg: {json.loads(msg)['type']}")
            except asyncio.TimeoutError:
                break

    print("\nTests complete.")

if __name__ == "__main__":
    asyncio.run(test_websocket())
