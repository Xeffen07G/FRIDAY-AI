import os
import tempfile
import time
import threading
from config.settings import settings
from .voice_pipeline import VoicePipeline

class VoiceOrchestrator:
    """Manages STT, TTS and Voice Activity Detection with production settings."""
    
    def __init__(self):
        self.pipeline = VoicePipeline(model_size="tiny.en")
        self._local = threading.local()
        
    def get_recent_metrics(self) -> dict:
        return getattr(self._local, "metrics", {"decode_ms": 0, "stt_ms": 0})
        
    def speech_to_text(self, webm_path: str) -> str:
        """Transcribes the provided webm file with Whisper tiny.en."""
        wav_path = webm_path + ".wav"
        decode_ms = 0
        try:
            import subprocess
            t_decode_start = time.time()
            
            print("INPUT:", webm_path)
            print("EXISTS:", os.path.exists(webm_path))
            if os.path.exists(webm_path):
                print("SIZE:", os.path.getsize(webm_path))

            try:
                subprocess.run(["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                process_path = wav_path
                decode_ms = int((time.time() - t_decode_start) * 1000)
                
                print("WAV EXISTS:", os.path.exists(wav_path))
                
                if os.path.exists(webm_path):
                    webm_size = os.path.getsize(webm_path)
                    print(f"WEBM SIZE: {webm_size}")
                else:
                    webm_size = 0
                    
                if os.path.exists(wav_path):
                    wav_size = os.path.getsize(wav_path)
                    print(f"WAV SIZE: {wav_size}")
                else:
                    wav_size = 0
                    
                if webm_size < 4000 or wav_size < 10000:
                    return "STT Error: Couldn't hear clearly. Tap mic and try again."
                        
            except subprocess.SubprocessError:
                return "STT Error: Invalid data found when processing input"
                
            t_stt_start = time.time()
            text = self.pipeline.speech_to_text(process_path)
            stt_ms = int((time.time() - t_stt_start) * 1000)
            
            self._local.metrics = {"decode_ms": decode_ms, "stt_ms": stt_ms}
            return text
        finally:
            if os.path.exists(webm_path):
                os.remove(webm_path)
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

