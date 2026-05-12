import { API_CONFIG } from '../config/api';

const API_BASE = `${API_CONFIG.BASE_URL}/api`;

let currentAudio = null;
let currentAudioUrl = null;

export const voiceService = {
  async transcribe(blob) {
    const formData = new FormData();
    formData.append('file', blob, 'recording.webm');

    try {
      const response = await fetch(`${API_BASE}/voice/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Transcription failed: ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error("voiceService.transcribe failed:", err);
      throw err;
    }
  },

  async speak(text) {
    if (!text) return;
    
    try {
      this.stop();

      const response = await fetch(`${API_BASE}/voice/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) throw new Error('Speech synthesis failed');

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      currentAudioUrl = audioUrl;

      const audio = new Audio();
      audio.src = audioUrl;
      audio.preload = "auto";
      currentAudio = audio;

      return new Promise((resolve, reject) => {
        audio.oncanplaythrough = () => {
          audio.play().catch(reject);
        };
        audio.onended = () => {
          this.cleanup();
          resolve();
        };
        audio.onerror = (e) => {
          this.cleanup();
          reject(e);
        };
      });
    } catch (err) {
      console.error("voiceService.speak failed:", err);
      throw err;
    }
  },

  stop() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.src = "";
      currentAudio.load();
      currentAudio = null;
    }
    this.cleanup();
  },

  cleanup() {
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      currentAudioUrl = null;
    }
  }
};
