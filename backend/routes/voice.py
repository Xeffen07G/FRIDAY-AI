from fastapi import APIRouter, UploadFile, File, Response, HTTPException
from pydantic import BaseModel
from voice.voice_orchestrator import voice_orchestrator

router = APIRouter()

class SpeakRequest(BaseModel):
    text: str

@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Convert uploaded audio file to text using Whisper."""
    try:
        audio_bytes = await file.read()
        text = voice_orchestrator.speech_to_text(audio_bytes)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speak")
async def speak_endpoint(request: SpeakRequest):
    """Convert text to speech audio stream using Piper."""
    try:
        audio_data = voice_orchestrator.text_to_speech(request.text)
        if not audio_data:
            raise HTTPException(status_code=500, detail="TTS generation failed")
        return Response(content=audio_data, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
