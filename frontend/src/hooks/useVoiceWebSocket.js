import { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

const WS_URL = API_CONFIG.ENDPOINTS.WS_VOICE;

export function useVoiceWebSocket(sessionId, onTranscript, onToken, onMetrics) {
  const [convState, setConvState] = useState('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [micEnergy, setMicEnergy] = useState(0);
  const [partialTranscript, setPartialTranscript] = useState('');
  const [events, setEvents] = useState([]);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const interruptEventRef = useRef(false);

  const addEvent = useCallback((type, data) => {
    setEvents(prev => [{
      id: Date.now() + Math.random(),
      timestamp: new Date().toLocaleTimeString(),
      type,
      data
    }, ...prev].slice(0, 50));
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
  useEffect(() => {
    let reconnectTimeout = null;
    let isUnmounted = false;

    const connectWebSocket = () => {
      if (isUnmounted) return;
      
      const url = new URL(WS_URL);
      if (sessionId) url.searchParams.set("session_id", sessionId);
      
      const ws = new WebSocket(url.toString());

      ws.onopen = () => {
        if (isUnmounted) { ws.close(); return; }
        setIsConnected(true);
        wsRef.current = ws;
        addEvent('SYS', { status: 'connected', session_id: sessionId });
      };

      ws.onmessage = (event) => {
        if (isUnmounted) return;
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
          case 'error':
            console.error("WS Voice Error:", msg.data);
            setConvState('idle');
            addEvent('ERR', msg.data);
            break;
          default: break;
        }
      };

      ws.onclose = () => {
        if (isUnmounted) return;
        setIsConnected(false);
        setConvState('idle');
        wsRef.current = null;
        addEvent('SYS', { status: 'disconnected' });
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        if (isUnmounted) return;
        addEvent('ERR', 'WebSocket connection error');
      };
    };

    connectWebSocket();

    return () => {
      isUnmounted = true;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [sessionId, onTranscript, onToken, onMetrics, addEvent, sendMsg, playNextInQueue]);

  const startRecording = useCallback(async () => {
    try {
      interrupt();
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
      });
      
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
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
                   if (!silenceTimer) silenceTimer = setTimeout(stopInternal, 600);
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

      recorder.start(500);
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

  return { convState, isConnected, isRecording, micEnergy, partialTranscript, startRecording, stopRecording, interrupt, events };
}
