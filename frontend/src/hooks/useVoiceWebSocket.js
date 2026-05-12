import { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

const WS_URL = API_CONFIG.ENDPOINTS.WS_VOICE;

export function useVoiceWebSocket(sessionId, onTranscript, onToken, onMetrics) {
  const [convState, setConvState] = useState('idle'); // idle, listening, transcribing, thinking, speaking
  const [isRecording, setIsRecording] = useState(false);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const interruptEventRef = useRef(false);

  const [isConnected, setIsConnected] = useState(false);
  const [micEnergy, setMicEnergy] = useState(0);
  const [partialTranscript, setPartialTranscript] = useState('');

  // Initialize WebSocket with Reconnection
  useEffect(() => {
    let reconnectTimeout = null;
    let isUnmounted = false;

    const connectWebSocket = () => {
      if (isUnmounted) return;
      console.log("Attempting to connect Voice WebSocket...");
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        if (isUnmounted) {
          ws.close();
          return;
        }
        console.log("Voice WebSocket CONNECTED successfully.");
        wsRef.current = ws;
        setIsConnected(true);
      };

      ws.onmessage = async (event) => {
        if (isUnmounted) return;
        const msg = JSON.parse(event.data);
        switch (msg.type) {
          case 'status': setConvState(msg.data); break;
          case 'transcript': 
            setPartialTranscript('');
            if (onTranscript) onTranscript(msg.data); 
            break;
          case 'transcript_partial': 
            setPartialTranscript(msg.data);
            break;
          case 'token': if (onToken) onToken(msg.data); break;
          case 'audio':
            audioQueueRef.current.push(msg.data);
            if (!isPlayingRef.current) playNextInQueue();
            break;
          case 'metrics': if (onMetrics) onMetrics(prev => ({...prev, ...msg.data})); break;
          case 'error':
            console.error("WS Voice Error:", msg.data);
            setConvState('idle');
            break;
          default: break;
        }
      };

      ws.onclose = (event) => {
        if (isUnmounted) return;
        console.warn(`Voice WebSocket DISCONNECTED (Code: ${event.code}). Reconnecting in 3s...`);
        setIsConnected(false);
        setConvState('idle');
        wsRef.current = null;
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        if (isUnmounted) return;
        console.error("Voice WebSocket ERROR:", err);
      };
    };

    connectWebSocket();

    return () => {
      isUnmounted = true;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [onTranscript, onToken, onMetrics]);

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
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "interrupt" }));
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.pause();
      audioContextRef.current.src = "";
    }
    
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setConvState('idle');
    
    setTimeout(() => { interruptEventRef.current = false; }, 200);
  }, []);

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

      // Local VAD for Barge-in and Auto-stop
      const actx = new AudioContext();
      const source = actx.createMediaStreamSource(stream);
      const analyser = actx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.5;
      source.connect(analyser);
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      let ambientVolume = 255;
      let hasSpoken = false;
      let silenceTimer = null;
      let maxListeningTimer = null;
      let bargeInFrames = 0;

      const stopInternal = () => {
          if (recorder.state !== 'inactive') recorder.stop();
      };

      const bargeInCheck = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a,b)=>a+b,0) / dataArray.length;
        setMicEnergy(volume);
        
        // Dynamically track ambient noise (lowest volume seen, decaying upwards slowly)
        if (volume < ambientVolume) ambientVolume = volume;
        else ambientVolume += 0.2; 
        
        const speechThreshold = Math.max(12, ambientVolume + 10);
        const silenceThreshold = Math.max(8, ambientVolume + 6);
        
        // Barge-in check (debounce 3 frames = 300ms)
        if (volume > speechThreshold + 5 && isPlayingRef.current) {
          bargeInFrames++;
          if (bargeInFrames >= 3) {
            console.log("Barge-in detected via local VAD (debounced)", { volume, speechThreshold });
            interrupt();
            bargeInFrames = 0;
          }
        } else {
          bargeInFrames = 0;
        }

        // Auto-stop logic (only arm if we aren't already speaking back)
        if (!isPlayingRef.current) {
           if (!hasSpoken && volume > speechThreshold) {
               hasSpoken = true;
               clearTimeout(maxListeningTimer);
           }
           
           if (hasSpoken) {
               if (volume < silenceThreshold) {
                   if (!silenceTimer) {
                       silenceTimer = setTimeout(() => {
                           console.log("Silence detected. Auto-stopping.");
                           stopInternal();
                       }, 600); // Accelerated from 1500ms to 600ms for realtime feel
                   }
               } else {
                   clearTimeout(silenceTimer);
                   silenceTimer = null;
               }
           }
        }
      }, 100);

      maxListeningTimer = setTimeout(() => {
          if (!hasSpoken) {
             console.log("No speech detected for 10s. Timing out.");
             stopInternal();
          }
      }, 10000);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
            audioChunks.push(e.data);
            
            // Streaming STT: Send partial chunk if WS is open
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                const reader = new FileReader();
                reader.readAsDataURL(e.data);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    wsRef.current.send(JSON.stringify({ 
                        type: "audio_chunk", 
                        data: base64data,
                        session_id: sessionId
                    }));
                };
            }
        }
      };

      recorder.onstop = async () => {
        clearInterval(bargeInCheck);
        clearTimeout(silenceTimer);
        clearTimeout(maxListeningTimer);
        actx.close();
        stream.getTracks().forEach(t => t.stop());
        setMicEnergy(0);
        
        const duration = Date.now() - recordingStartTime;
        
        if (audioChunks.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const blob = new Blob(audioChunks, { type: "audio/webm" });
          
          if (blob.size < 2500 || duration < 300) {
            console.warn(`Dropping tiny audio payload: ${blob.size} bytes, ${duration}ms`);
            wsRef.current.send(JSON.stringify({ type: "audio_cancel" }));
          } else {
            console.log(`Sending audio final: ${blob.size} bytes, ~${duration}ms`);
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = () => {
              const base64data = reader.result.split(',')[1];
              wsRef.current.send(JSON.stringify({ 
                type: "audio_final", 
                data: base64data,
                session_id: sessionId,
                metrics: { blob_size: blob.size, capture_duration: duration }
              }));
            };
          }
        }
        setIsRecording(false);
      };

      recorder.start(500); // Send chunks every 500ms for streaming STT
      setIsRecording(true);
      setConvState('listening');

    } catch (err) {
      console.error("Failed to start recording:", err);
      setIsRecording(false);
      setConvState('idle');
    }
  }, [sessionId, interrupt]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  return { convState, isConnected, isRecording, micEnergy, partialTranscript, startRecording, stopRecording, interrupt };
}
