import os
import subprocess
from faster_whisper import WhisperModel
from core.logger import get_logger

logger = get_logger("voice.pipeline")

class VoicePipeline:
    """Handles Speech-to-Text and Text-to-Speech."""
    def __init__(self, model_size="base.en"):
        # Load faster-whisper model
        self.stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        # Piper TTS path - using absolute paths for Windows stability
        self.piper_path = os.path.join(os.getcwd(), "piper.exe")
        self.voice_model_path = os.path.join(os.getcwd(), "backend", "en_US-lessac-medium.onnx")
        
    def speech_to_text(self, audio_file_path: str) -> str:
        """Converts an audio file to text using faster-whisper with VAD."""
        try:
            # STT Stabilization parameters
            segments, info = self.stt_model.transcribe(
                audio_file_path, 
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=1000, speech_pad_ms=400),
                language="en",
                initial_prompt="User speaking to assistant clearly.",
                condition_on_previous_text=False,
                no_speech_threshold=0.55,
                log_prob_threshold=-1.0
            )
            text = " ".join([segment.text for segment in segments]).strip()
            
            # Confidence thresholding / noise filtering
            if len(text) < 2 or text.lower() in ["thank you.", "you", "bye.", "okay.", "ah.", "oh."]:
                return ""
            
            return text
        except Exception as e:
            return f"STT Error: {str(e)}"
            
    def text_to_speech(self, text: str, output_file: str = "output.wav"):
        """Converts text to speech using Piper TTS."""
        try:
            # Use subprocess with input to avoid shell escaping issues
            subprocess.run(
                [self.piper_path, "--model", self.voice_model_path, "--output_file", output_file],
                input=text.encode('utf-8'),
                check=True,
                capture_output=True
            )
            return output_file
        except Exception as e:
            logger.error(f"TTS Error: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"Piper Stderr: {e.stderr.decode()}")
            return None
