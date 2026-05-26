const BACKEND_PORT = "8000";
const BASE_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// Dynamically generate the websocket URL using window.location.hostname and port 8000
const getWsUrl = () => {
  const hostname = (typeof window !== 'undefined' && window.location && window.location.hostname) 
    ? window.location.hostname 
    : '127.0.0.1';
  return `ws://${hostname}:${BACKEND_PORT}`;
};

const WS_URL = getWsUrl();

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
