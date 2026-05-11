import logging

logger = logging.getLogger("friday.voice")

class VoiceOrchestrator:
    """Manages STT, TTS and Voice Activity Detection."""
    
    def __init__(self):
        logger.info("Voice Pipeline initialized (Stub).")

    def speech_to_text(self, audio_data):
        """Converts audio bytes to text."""
        # TODO: Integrate faster-whisper
        return "Audio input detected (STT not yet implemented)"

    def text_to_speech(self, text):
        """Converts text to audio stream."""
        # TODO: Integrate Piper or gTTS
        return None

voice_orchestrator = VoiceOrchestrator()
