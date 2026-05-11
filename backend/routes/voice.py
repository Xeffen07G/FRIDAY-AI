from fastapi import APIRouter, UploadFile, File
from backend.voice.voice_orchestrator import voice_orchestrator

router = APIRouter()

@router.post("/stt")
async def stt_endpoint(file: UploadFile = File(...)):
    """Convert uploaded audio file to text."""
    audio_bytes = await file.read()
    text = voice_orchestrator.speech_to_text(audio_bytes)
    return {"text": text}

@router.get("/tts")
async def tts_endpoint(text: str):
    """Convert text to speech audio stream."""
    # This would return a StreamingResponse with audio/wav
    return {"message": "TTS stream for: " + text}
