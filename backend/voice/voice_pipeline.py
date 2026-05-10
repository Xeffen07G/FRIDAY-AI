import os
import subprocess
from faster_whisper import WhisperModel

class VoicePipeline:
    """Handles Speech-to-Text and Text-to-Speech."""
    def __init__(self, model_size="tiny.en"):
        # Load faster-whisper model
        self.stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        # Piper TTS path (assuming binary is available or installed)
        self.piper_path = "piper"
        self.voice_model_path = "en_US-lessac-medium.onnx"
        
    def speech_to_text(self, audio_file_path: str) -> str:
        """Converts an audio file to text using faster-whisper."""
        try:
            segments, info = self.stt_model.transcribe(audio_file_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            return f"STT Error: {str(e)}"
            
    def text_to_speech(self, text: str, output_file: str = "output.wav"):
        """Converts text to speech using Piper TTS."""
        try:
            # We use subprocess to call piper TTS
            command = f"echo '{text}' | {self.piper_path} --model {self.voice_model_path} --output_file {output_file}"
            subprocess.run(command, shell=True, check=True)
            return output_file
        except Exception as e:
            print(f"TTS Error: {str(e)}")
            return None
