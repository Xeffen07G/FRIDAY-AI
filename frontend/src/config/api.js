const BACKEND_PORT = "8001";
const BASE_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const WS_URL = `ws://127.0.0.1:${BACKEND_PORT}`;

export const API_CONFIG = {
  BASE_URL,
  WS_URL,
  ENDPOINTS: {
    SESSIONS: `${BASE_URL}/api/sessions`,
    MEMORIES: `${BASE_URL}/api/memories`,
    CHAT: `${BASE_URL}/api/chat`,
    VOICE_TRANSCRIBE: `${BASE_URL}/api/voice/transcribe`,
    VOICE_SPEAK: `${BASE_URL}/api/voice/speak`,
    WS_VOICE: `${WS_URL}/api/ws/voice`,
    HEALTH: `${BASE_URL}/api/health/deep`
  }
};
