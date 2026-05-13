import asyncio
import json
import uuid
import time
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from orchestrator.orchestrator import friday_orchestrator
from voice.voice_orchestrator import voice_orchestrator
from config.settings import settings
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger("ws_voice")
router = APIRouter()

class VoiceSession:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.is_active = True
        self.interrupt_event = asyncio.Event()
        self.request_id = ""
        self.audio_buffer = bytearray()
        self.last_partial_transcript = ""

    async def send_status(self, status: str):
        await self.websocket.send_json({"type": "status", "data": status})

    async def send_token(self, token: str):
        await self.websocket.send_json({"type": "token", "data": token})

    async def send_audio(self, audio_base64: str):
        await self.websocket.send_json({"type": "audio", "data": audio_base64})

    async def send_metrics(self, metrics: dict):
        await self.websocket.send_json({"type": "metrics", "data": metrics})

@router.websocket("/api/ws/voice")
async def voice_websocket(websocket: WebSocket):
    try:
        await websocket.accept()
        session = VoiceSession(websocket)
        logger.info(f"[WS_VOICE] Client connected: {websocket.client}")
    except Exception as e:
        logger.error(f"[WS_VOICE] Failed to accept WebSocket: {e}")
        return

    query_params = websocket.query_params
    chat_session_id = query_params.get("session_id", str(uuid.uuid4()))
    event_bus.emit("network", "websocket_connected", {"session_id": chat_session_id})

    # Phase 3: Session Reliability - Heartbeat mechanism
    async def run_heartbeat():
        while session.is_active:
            try:
                await websocket.send_json({"type": "ping", "ts": time.time()})
                await asyncio.sleep(30)
            except Exception:
                break
    
    heartbeat_task = asyncio.create_task(run_heartbeat())

    # Phase 5: Observable Runtime - Push events to UI
    async def event_pusher(event):
        if not session.is_active: return
        try:
            # We only push events relevant to this session or global desktop activity
            if event.get("component") in ["brain", "voice", "desktop", "network"]:
                await websocket.send_json({
                    "type": "system_event",
                    "data": event
                })
        except Exception:
            pass
            
    event_bus.subscribe(event_pusher)

    try:
        while True:
            # Receive message from frontend
            message = await websocket.receive_text()
            data = json.loads(message)

            if data["type"] == "interrupt":
                logger.info("Barge-in detected: interrupting playback/generation")
                session.interrupt_event.set()
                continue

            if data["type"] == "audio_chunk":
                try:
                    chunk_bytes = base64.b64decode(data["data"])
                    session.audio_buffer.extend(chunk_bytes)
                except Exception as e:
                    logger.error(f"Error handling audio_chunk: {e}")

            if data["type"] == "audio_final":
                logger.info(f"Received audio_final (buffer len: {len(session.audio_buffer)})")
                session.request_id = str(uuid.uuid4())[:8]
                session.interrupt_event.clear()
                
                audio_to_process = bytes(session.audio_buffer)
                session.audio_buffer.clear()
                
                if len(audio_to_process) > 1000:
                    asyncio.create_task(process_voice_request(session, audio_to_process, chat_session_id))
                continue

            if data["type"] == "audio_cancel":
                session.audio_buffer.clear()
                continue
                
    except WebSocketDisconnect:
        session.is_active = False
        event_bus.emit("network", "websocket_disconnected", {"session_id": chat_session_id})
        logger.info(f"[WS_VOICE] Client disconnected: {chat_session_id}")
    except Exception as e:
        session.is_active = False
        logger.error(f"[WS_VOICE] Runtime Error: {e}")
        event_bus.emit("network", "websocket_error", {"session_id": chat_session_id, "error": str(e)})

async def process_partial_transcript(session: VoiceSession):
    """Generates a partial transcript hypothesis for UI feedback."""
    if not session.audio_buffer or len(session.audio_buffer) < 16000:
        return
        
    try:
        # Clone buffer to avoid race conditions
        buffer_copy = bytes(session.audio_buffer)
        transcript = await asyncio.to_thread(voice_orchestrator.speech_to_text, buffer_copy)
        
        if transcript and transcript != session.last_partial_transcript:
            session.last_partial_transcript = transcript
            await session.websocket.send_json({
                "type": "transcript_partial", 
                "data": transcript 
            })
    except Exception as e:
        logger.debug(f"Partial STT failed (skipping): {e}")

async def process_voice_request(session: VoiceSession, audio_bytes: bytes, chat_session_id: str):
    try:
        # 1. Transcribe
        await session.send_status("transcribing")
        event_bus.emit("voice", "stt_start", {"request_id": session.request_id})
        stt_start = time.time()
        transcript = await asyncio.to_thread(voice_orchestrator.speech_to_text, audio_bytes)
        stt_ms = int((time.time() - stt_start) * 1000)
        event_bus.emit("voice", "stt_finish", {"request_id": session.request_id, "transcript": transcript, "stt_ms": stt_ms})
        
        if not transcript or transcript.startswith("STT Error"):
            await session.send_status("idle")
            return

        await session.websocket.send_json({"type": "transcript", "data": transcript})
        
        # 2. LLM Stream
        await session.send_status("thinking")
        event_bus.emit("brain", "llm_start", {"request_id": session.request_id, "prompt": transcript})
        full_response = ""
        current_sentence = ""
        
        # TTS Queue for ordered playback
        tts_queue = asyncio.Queue()
        async def tts_worker():
            while True:
                text_to_speak = await tts_queue.get()
                if text_to_speak is None:
                    break
                if not session.interrupt_event.is_set():
                    await synthesize_and_send(session, text_to_speak, session.request_id)
                tts_queue.task_done()
                
        worker_task = asyncio.create_task(tts_worker())
        
        # We wrap the orchestrator stream
        async for chunk in friday_orchestrator.process_stream(chat_session_id, transcript, session.request_id):
            if session.interrupt_event.is_set():
                logger.info(f"[REQ:{session.request_id}] LLM Interrupted by user.")
                break

            # Handle status/metrics packets from orchestrator
            if chunk.startswith("[[STATUS:"): continue
            if chunk.startswith("[[METRICS:"): 
                metrics_data = json.loads(chunk.replace("[[METRICS:", "").replace("]]", ""))
                metrics_data["stt_ms"] = stt_ms
                await session.send_metrics(metrics_data)
                continue

            full_response += chunk
            current_sentence += chunk
            await session.send_token(chunk)

            # Progressive TTS: Synthesize on punctuation boundaries or early chunk length
            if any(punct in chunk for punct in [".", "!", "?", "\n", ";", ":"]) and len(current_sentence.strip()) > 5:
                await session.send_status("speaking")
                sentence_to_speak = current_sentence.strip()
                current_sentence = ""
                await tts_queue.put(sentence_to_speak)

        # Final flush for any remaining text
        if current_sentence.strip() and not session.interrupt_event.is_set():
            await session.send_status("speaking")
            await tts_queue.put(current_sentence.strip())

        # Wait for TTS queue to finish
        await tts_queue.put(None)
        await worker_task
        
        await session.send_status("idle")

    except Exception as e:
        logger.error(f"Voice request processing failed: {e}")
        await session.websocket.send_json({"type": "error", "data": str(e)})
        await session.send_status("idle")

async def synthesize_and_send(session: VoiceSession, text: str):
    """Synthesizes text and sends as base64 audio over WebSocket."""
    if session.interrupt_event.is_set(): return
    
    try:
        # TTS synthesis
        tts_start = time.time()
        audio_data = await asyncio.to_thread(voice_orchestrator.text_to_speech, text)
        tts_ms = int((time.time() - tts_start) * 1000)
        
        if audio_data and not session.interrupt_event.is_set():
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            await session.websocket.send_json({"type": "audio", "data": audio_b64})
            await session.send_metrics({"tts_ms": tts_ms, "tts_chunk_len": len(text)})
    except Exception as e:
        logger.error(f"TTS synthesis/send failed: {e}")
