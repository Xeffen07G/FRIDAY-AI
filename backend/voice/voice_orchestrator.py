import os
import tempfile
from config.settings import settings
from .voice_pipeline import VoicePipeline

class VoiceOrchestrator:
    """Manages STT, TTS and Voice Activity Detection with production settings."""
    
    def __init__(self):
        self.pipeline = VoicePipeline(model_size="base.en")
        
    def speech_to_text(self, audio_bytes: bytes) -> str:
        """Saves bytes to temp file and transcribes with Whisper base.en."""
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False, dir=settings.TEMP_AUDIO_PATH) as tf:
            tf.write(audio_bytes)
            temp_path = tf.name
            
        wav_path = temp_path + ".wav"
        try:
            import subprocess
            try:
                subprocess.run(["ffmpeg", "-y", "-i", temp_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                process_path = wav_path
                
                # Payload validation
                if os.path.exists(wav_path):
                    size = os.path.getsize(wav_path)
                    # 16000Hz * 2 bytes/sample * 1 channel = 32000 bytes/sec
                    duration_sec = max(0, (size - 44) / 32000)
                    import logging
                    logging.getLogger("voice_orchestrator").info(f"Decoded payload duration: {duration_sec:.2f}s ({size} bytes)")
                    if duration_sec < 0.2:
                        return "" # Drop extreme noise payloads
                        
            except (subprocess.SubprocessError, FileNotFoundError):
                process_path = temp_path
                
            text = self.pipeline.speech_to_text(process_path)
            return text
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)

    def text_to_speech(self, text: str):
        """Generates audio file for the given text."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=settings.TEMP_AUDIO_PATH) as tf:
            output_path = tf.name
            
        try:
            result_path = self.pipeline.text_to_speech(text, output_path)
            if result_path:
                with open(result_path, "rb") as f:
                    return f.read()
            return None
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

voice_orchestrator = VoiceOrchestrator()
