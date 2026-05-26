import { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

const WS_URL = API_CONFIG.ENDPOINTS.WS_VOICE;

export function useVoiceWebSocket(sessionId, onTranscript, onToken, onMetrics, onDisconnect) {
  const [convState, setConvState] = useState('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [micEnergy, setMicEnergy] = useState(0);
  const [partialTranscript, setPartialTranscript] = useState('');
  const [events, setEvents] = useState([]);
  const [voiceError, setVoiceError] = useState(null);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const interruptEventRef = useRef(false);

  const addEvent = useCallback((type, data) => {
    setEvents(prev => {
      if (prev.length > 0) {
        const last = prev[0];
        const isDuplicate = last.type === type && JSON.stringify(last.data) === JSON.stringify(data);
        if (isDuplicate) return prev;
      }
      return [{
        id: Date.now() + Math.random(),
        timestamp: new Date().toLocaleTimeString(),
        type,
        data
      }, ...prev].slice(0, 50);
    });
  }, []);

  const sendMsg = useCallback((type, payload = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const msg = { type, ...payload };
      wsRef.current.send(JSON.stringify(msg));
      if (type !== 'pong' && type !== 'audio_chunk') {
        addEvent('SEND', msg);
      }
    }
  }, [addEvent]);

  const playNextInQueue = useCallback(async () => {
    if (audioQueueRef.current.length === 0 || interruptEventRef.current) {
      isPlayingRef.current = false;
      if (!interruptEventRef.current && convState === 'speaking') setConvState('idle');
      return;
    }

    isPlayingRef.current = true;
    const base64Audio = audioQueueRef.current.shift();
    const audioData = Uint8Array.from(atob(base64Audio), c => c.charCodeAt(0));
    const blob = new Blob([audioData], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    
    const audio = new Audio(url);
    audio.onended = () => {
      URL.revokeObjectURL(url);
      playNextInQueue();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      playNextInQueue();
    };

    audioContextRef.current = audio;
    await audio.play().catch(e => {
        console.error("Audio playback failed", e);
        playNextInQueue();
    });
  }, [convState]);

  const interrupt = useCallback(() => {
    if (!isPlayingRef.current && audioQueueRef.current.length === 0) return;
    console.log("useVoiceWS: INTERRUPT triggered");
    interruptEventRef.current = true;
    
    sendMsg("interrupt");
    
    if (audioContextRef.current) {
      audioContextRef.current.pause();
      audioContextRef.current.src = "";
    }
    
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setConvState('idle');
    addEvent('UI', { action: 'interrupt' });
    
    setTimeout(() => { interruptEventRef.current = false; }, 200);
  }, [sendMsg, addEvent]);

  // Initialize WebSocket with Reconnection
  // WS_RECONNECT_MAX: Stop trying after 5 consecutive failures
  // Backoff: 1s → 2s → 4s → 8s → 16s
  useEffect(() => {
    if (wsRef.current) return; // One websocket only
    
    let reconnectTimeout = null;
    let isUnmounted = false;
    let reconnectAttempt = 0;
    const WS_RECONNECT_MAX = 5;
    const BACKOFF_SCHEDULE = [1000, 2000, 4000, 8000, 16000];

    const connectWebSocket = () => {
      if (isUnmounted) return;
      if (reconnectAttempt >= WS_RECONNECT_MAX) {
        console.warn(`[WS_DIAG] Max reconnect attempts (${WS_RECONNECT_MAX}) reached. Stopping.`);
        setIsConnected(false);
        addEvent('ERR', { status: 'max_reconnect_reached' });
        return;
      }
      
      // Enforce single connection — close any stale socket first
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      
      const url = new URL(WS_URL);
      if (sessionId) url.searchParams.set("session_id", sessionId);
      
      console.log(`[WS_DIAG] Attempting connection to: ${url.toString()} (attempt ${reconnectAttempt + 1}/${WS_RECONNECT_MAX})`);
      
      const ws = new WebSocket(url.toString());

      ws.onopen = () => {
        console.log(`[WS_DIAG] Connection OPEN: ${url.toString()}`);
        if (isUnmounted) { ws.close(); return; }
        setIsConnected(true);
        wsRef.current = ws;
        reconnectAttempt = 0; // Reset on successful handshake
        addEvent('SYS', { status: 'connected', session_id: sessionId });
      };

      ws.onmessage = (event) => {
        if (isUnmounted) return;
        console.log("WS MESSAGE", event.data);
        const msg = JSON.parse(event.data);
        
        if (msg.type !== 'ping' && msg.type !== 'token') {
          addEvent('RECV', msg);
        }

        switch (msg.type) {
          case 'ping': sendMsg('pong', { ts: Date.now() }); break;
          case 'status': setConvState(msg.data); break;
          case 'transcript': 
            setPartialTranscript('');
            if (onTranscript) onTranscript(msg.data); 
            break;
          case 'transcript_partial': setPartialTranscript(msg.data); break;
          case 'token': if (onToken) onToken(msg.data); break;
          case 'audio':
            audioQueueRef.current.push(msg.data);
            if (!isPlayingRef.current) playNextInQueue();
            break;
          case 'metrics': if (onMetrics) onMetrics(prev => ({...prev, ...msg.data})); break;
          case 'system_event': 
            addEvent(msg.data.level || 'SYS', msg.data);
            if (msg.data.type === 'ui_focus_toggle') {
                window.dispatchEvent(new CustomEvent('friday_focus_toggle', { detail: msg.data.data }));
            }
            if (msg.data.type === 'ptt_event') {
                window.dispatchEvent(new CustomEvent('friday_ptt', { detail: msg.data.data }));
            }
            break;
          case 'error':
            console.error("WS Voice Error:", msg.data);
            setConvState('idle');
            setVoiceError(msg.data);
            addEvent('ERR', msg.data);
            if (msg.data.includes("Couldn't hear clearly")) {
                setTimeout(() => {
                    if (!isUnmounted) window.dispatchEvent(new CustomEvent('friday_ptt', { detail: { state: 'pressed' } }));
                }, 1500);
            }
            break;
          default: break;
        }
      };

      ws.onclose = (event) => {
        console.warn(`[WS_DIAG] Connection CLOSED. Code: ${event.code}, Reason: ${event.reason || 'none'}`);
        if (isUnmounted) return;
        setIsConnected(false);
        setConvState('idle');
        wsRef.current = null;
        addEvent('SYS', { status: 'disconnected' });
        
        if (onDisconnect) {
          onDisconnect();
        }
        
        const delay = BACKOFF_SCHEDULE[Math.min(reconnectAttempt, BACKOFF_SCHEDULE.length - 1)];
        reconnectAttempt++;
        console.log(`[WS_DIAG] Reconnecting in ${delay}ms (attempt ${reconnectAttempt}/${WS_RECONNECT_MAX})`);
        reconnectTimeout = setTimeout(connectWebSocket, delay);
      };

      ws.onerror = (err) => {
        console.error(`[WS_DIAG] Connection ERROR:`, err);
        if (isUnmounted) return;
        addEvent('ERR', 'WebSocket connection error');
      };
    };

    connectWebSocket();

    return () => {
      isUnmounted = true;
      clearTimeout(reconnectTimeout);
      console.log("WS CLOSED");
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setVoiceError(null);
      interrupt();
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          channelCount: 1,
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true 
        } 
      });
      
      const recorder = new MediaRecorder(stream, { 
        mimeType: "audio/webm;codecs=opus",
        audioBitsPerSecond: 64000
      });
      mediaRecorderRef.current = recorder;
      const audioChunks = [];
      const recordingStartTime = Date.now();

      const actx = new AudioContext();
      const source = actx.createMediaStreamSource(stream);
      const analyser = actx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      let ambientVolume = 255;
      let hasSpoken = false;
      let silenceTimer = null;
      let bargeInFrames = 0;

      const stopInternal = () => { if (recorder.state !== 'inactive') recorder.stop(); };

      const bargeInCheck = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a,b)=>a+b,0) / dataArray.length;
        setMicEnergy(volume);
        
        if (volume < ambientVolume) ambientVolume = volume;
        else ambientVolume += 0.2; 
        
        const speechThreshold = Math.max(12, ambientVolume + 10);
        const silenceThreshold = Math.max(8, ambientVolume + 6);
        
        if (volume > speechThreshold + 5 && isPlayingRef.current) {
          bargeInFrames++;
          if (bargeInFrames >= 3) {
            interrupt();
            bargeInFrames = 0;
          }
        } else { bargeInFrames = 0; }

        if (!isPlayingRef.current) {
           if (!hasSpoken && volume > speechThreshold) { hasSpoken = true; }
           if (hasSpoken) {
               if (volume < silenceThreshold) {
                   if (!silenceTimer) silenceTimer = setTimeout(stopInternal, 700);
               } else {
                   clearTimeout(silenceTimer);
                   silenceTimer = null;
               }
           }
        }
      }, 100);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
            audioChunks.push(e.data);
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                const reader = new FileReader();
                reader.readAsDataURL(e.data);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    sendMsg("audio_chunk", { data: base64data, session_id: sessionId });
                };
            }
        }
      };

      recorder.onstop = async () => {
        clearInterval(bargeInCheck);
        clearTimeout(silenceTimer);
        actx.close();
        stream.getTracks().forEach(t => t.stop());
        setMicEnergy(0);
        
        const duration = Date.now() - recordingStartTime;
        if (audioChunks.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const blob = new Blob(audioChunks, { type: "audio/webm" });
          if (blob.size < 2500 || duration < 300) {
            sendMsg("audio_cancel");
          } else {
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = () => {
              const base64data = reader.result.split(',')[1];
              sendMsg("audio_final", { 
                data: base64data, 
                session_id: sessionId,
                metrics: { blob_size: blob.size, capture_duration: duration }
              });
            };
          }
        }
        setIsRecording(false);
      };

      recorder.start(250);
      setIsRecording(true);
      setConvState('listening');
      addEvent('UI', { action: 'start_recording' });

    } catch (err) {
      console.error("Failed to start recording:", err);
      setIsRecording(false);
      setConvState('idle');
    }
  }, [sessionId, interrupt, sendMsg, addEvent]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      addEvent('UI', { action: 'stop_recording_manual' });
    }
  }, [addEvent]);

  useEffect(() => {
    if (!voiceError) return;
    const t = setTimeout(() => {
      if (!isUnmountedRef.current) setVoiceError(null);
    }, 2500);
    return () => clearTimeout(t);
  }, [voiceError]);

  return { convState, isConnected, isRecording, micEnergy, partialTranscript, voiceError, startRecording, stopRecording, interrupt, events };
}
