import { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

function sanitizeFrontText(text) {
  if (!text) return "";
  
  let cleaned = text;
  
  // Strip backend technical markers
  cleaned = cleaned.replace(/\[GENERATIVE_RESPONSE\]\s*/g, "");
  cleaned = cleaned.replace(/\[DETERMINISTIC_RESPONSE\]\s*/g, "");
  
  // Prohibited theatrical patterns
  const forbiddenPatterns = [
    /initiating\s+protocols?/gi,
    /identity\s+verification\s+complete/gi,
    /identity\s+verification\s+successful/gi,
    /identity\s+confirmed/gi,
    /executing\s+cognitive\s+remediation\s+workflow/gi,
    /executing\s+cognitive\s+process/gi,
    /analyzing\s+your\s+request\s+through\s+layered\s+cognition/gi,
    /greetings\s+human/gi,
    /future\s+capability\s+hooks?/gi,
    /simulated\s+operation/gi,
    /according\s+to\s+operational\s+framework/gi,
    /capability\s+hooks?/gi,
    /orchestration\s+layer\s+initialized/gi,
    /system\s+protocols\s+active/gi,
    /layered\s+cognition/gi,
    /advanced\s+engineering\s+runtime/gi,
    /system\s+narration/gi,
    /permissions\s+verified/gi,
    /background\s+cognition/gi,
    /system\s+analysis\s+complete/gi,
    /operational\s+status/gi,
    /as\s+an\s+ai\s+assistant/gi,
    /cognition\s+evolving/gi,
    /initiating\s+system/gi
  ];
  
  for (const pattern of forbiddenPatterns) {
    cleaned = cleaned.replace(pattern, "");
  }
  
  // Standalone keywords
  cleaned = cleaned.replace(/\binitiating\b/gi, "");
  cleaned = cleaned.replace(/\bprotocols?\b/gi, "");
  cleaned = cleaned.replace(/\bsimulated\b/gi, "");
  
  // Conversational prefix cleanup
  cleaned = cleaned.replace(/^(hello|hi|hey|greetings|dear user|sure|of course|certainly)(,?\s+there)?(!|\.|\?|,)?\s*/gi, "");

  // Adaptive verbosity
  const lower = cleaned.toLowerCase().trim();
  if (lower === "vscode" || lower === "visual studio code") {
    return "vscode opened";
  }
  if (lower === "calc" || lower === "calculator") {
    return "calculator opened";
  }
  if (lower === "chrome") {
    return "chrome opened";
  }
  if (lower === "hello" || lower === "greetings") {
    return "hello";
  }
  
  // Clean whitespace and dots
  cleaned = cleaned.replace(/\s+/g, " ");
  cleaned = cleaned.replace(/\.+/g, ".");
  cleaned = cleaned.trim();
  
  return cleaned;
}

export function useChat() {
  // 1. State Initializations
  const [sessions, setSessions] = useState([]);
  const [semanticMemories, setSemanticMemories] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(() => localStorage.getItem('friday_session_id') || null);
  const [messages, setMessages] = useState([]);
  const [renderLimit, setRenderLimit] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => localStorage.getItem('friday_sidebar_open') !== 'false');
  const [status, setStatus] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [isScrolledUp, setIsScrolledUp] = useState(false);

  useEffect(() => {
    localStorage.setItem('friday_sidebar_open', isSidebarOpen ? 'true' : 'false');
  }, [isSidebarOpen]);

  // 2. Ref Initializations
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const sendingRef = useRef(false);
  const scrollToBottomRef = useRef(null);
  const isFetchingSessionsRef = useRef(false);
  const activeLeaseRef = useRef(null);
  const lastRequestRef = useRef({ timestamp: 0, text: "" });
  const activeStreamsCountRef = useRef(0);
  const sessionScrollOffsetsRef = useRef({});

  // 3. Basic Utility Callbacks
  // Use a ref-stable pattern to prevent TDZ crashes in the
  // fetchSessions → switchSession → scrollToBottom dependency chain.
  const scrollToBottom = useCallback((behavior = 'auto') => {
    const container = chatContainerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, []);

  // Keep ref in sync so consumers outside the hook can call it safely
  scrollToBottomRef.current = scrollToBottom;

  // 4. Standalone Callbacks
  const fetchSemanticMemories = useCallback(async () => {
    try {
      const res = await fetch(`${API_CONFIG.ENDPOINTS.MEMORIES}/workspace`);
      const data = await res.json();
      setSemanticMemories(data);
    } catch (err) {
      console.error("Failed to fetch workspace memories", err);
    }
  }, []);

  const deleteSemanticMemory = useCallback(async (id) => {
    try {
      await fetch(`${API_CONFIG.ENDPOINTS.MEMORIES}/${id}`, { method: 'DELETE' });
      setSemanticMemories(prev => prev.filter(m => m.id !== id));
    } catch (err) {
      console.error("Failed to delete memory", err);
    }
  }, []);

  const cancel_generation = useCallback(() => {
    console.log("Unified cancel_generation() invoked");
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // Completion state fix: force states false
    setIsLoading(false); // setThinking(false)
    setStatus(''); // setSpeaking(false)
    
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.sender === 'friday' && lastMsg.streaming) {
        const next = [...prev];
        next[next.length - 1] = { ...lastMsg, streaming: false };
        return next;
      }
      return prev;
    });
    
    // Unified cancel path handles all stream cleanup
    if (currentSessionId) {
      fetch(`${API_CONFIG.ENDPOINTS.CHAT}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId })
      }).catch((err) => console.error("Cancel generation backend notification failed:", err));
    }
    
    // Invalidate lease
    activeLeaseRef.current = null;
  }, [currentSessionId]);

  const interrupt = useCallback(() => {
    cancel_generation();
  }, [cancel_generation]);

  // 5. Core Session Management Callbacks (ordered by dependency)
  const createNewSession = useCallback(async () => {
    try {
      const res = await fetch(API_CONFIG.ENDPOINTS.SESSIONS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: "New Chat" })
      });
      const data = await res.json();
      setSessions(prev => [data, ...prev]);
      setCurrentSessionId(data.id);
      setMessages([{ id: Date.now(), sender: 'friday', text: 'Ready when you are.' }]);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const switchSession = useCallback(async (id) => {
    // Save scroll position of current session before switching
    if (currentSessionId && chatContainerRef.current) {
      sessionScrollOffsetsRef.current[currentSessionId] = chatContainerRef.current.scrollTop;
      console.log(`[SCROLL_PERSIST] Saved scroll position ${chatContainerRef.current.scrollTop} for session ${currentSessionId}`);
    }

    // 6. SESSION TRANSITION CONTRACT
    cancel_generation(); // abort stream
    setCurrentSessionId(id); // change session
    setError(null);
    setMessages([]); // flush pending state
    setRenderLimit(100);
    try {
      const res = await fetch(`${API_CONFIG.ENDPOINTS.SESSIONS}/${id}/messages`);
      const data = await res.json();
      if (data.length === 0) {
        setMessages([{ id: Date.now(), sender: 'friday', text: 'Ready when you are.' }]);
      } else {
        setMessages(data);
      }
      
      // Restore scroll position or scroll to bottom
      requestAnimationFrame(() => {
        const savedOffset = sessionScrollOffsetsRef.current[id];
        if (savedOffset !== undefined && chatContainerRef.current) {
          chatContainerRef.current.scrollTop = savedOffset;
          console.log(`[SCROLL_PERSIST] Restored scroll position ${savedOffset} for session ${id}`);
        } else {
          scrollToBottomRef.current?.('auto');
        }
      });
    } catch (err) {
      console.error(err);
    }
  }, [currentSessionId, cancel_generation]);

  const fetchSessions = useCallback(async () => {
    if (isFetchingSessionsRef.current) return; // ADVERSARIAL FIX: Prevent StrictMode double-fetch race causing duplicate sessions
    isFetchingSessionsRef.current = true;
    try {
      const res = await fetch(API_CONFIG.ENDPOINTS.SESSIONS);
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const data = await res.json();
      const sessionArray = Array.isArray(data) ? data : [];
      setSessions(sessionArray);
      
      if (sessionArray.length > 0) {
        const savedId = localStorage.getItem('friday_session_id');
        const activeId = (savedId && sessionArray.find(s => s.id === savedId)) ? savedId : sessionArray[0].id;
        switchSession(activeId);
      } else {
        createNewSession();
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setError("Failed to load sessions. Check backend connection.");
    } finally {
      isFetchingSessionsRef.current = false;
    }
  }, [switchSession, createNewSession]);

  const deleteSession = useCallback(async (id, e) => {
    if (e) e.stopPropagation();
    
    console.log(`[DELETE_TX] Starting delete transaction for session: ${id}`);
    
    // 1. cancel
    cancel_generation();
    
    try {
      // 2. await delete
      const res = await fetch(`${API_CONFIG.ENDPOINTS.SESSIONS}/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Delete failed on server");
      
      // 3. clear state
      setMessages([]);
      setError(null);
      setStatus('');
      
      // Find next session to navigate to
      const remainingSessions = sessions.filter(s => s.id !== id);
      setSessions(remainingSessions);
      
      let nextSessionId = null;
      if (currentSessionId === id) {
        if (remainingSessions.length > 0) {
          nextSessionId = remainingSessions[0].id;
        }
      } else {
        nextSessionId = currentSessionId;
      }
      
      // 4. navigate
      if (nextSessionId) {
        setCurrentSessionId(nextSessionId);
        
        // 5. hydrate
        const messagesRes = await fetch(`${API_CONFIG.ENDPOINTS.SESSIONS}/${nextSessionId}/messages`);
        const data = await messagesRes.json();
        if (data.length === 0) {
          setMessages([{ id: Date.now(), sender: 'friday', text: 'Ready when you are.' }]);
        } else {
          setMessages(data);
        }
        requestAnimationFrame(() => scrollToBottomRef.current?.('auto'));
      } else {
        // If no sessions remain, create a new one (which will handle its own hydration)
        await createNewSession();
      }
      
      console.log(`[DELETE_TX] Session delete transaction completed successfully.`);
    } catch (err) {
      console.error("[DELETE_TX] Transaction failed:", err);
      setError("Failed to delete session.");
    }
  }, [currentSessionId, sessions, cancel_generation, createNewSession]);

  // 6. Messaging execution callback
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading || !currentSessionId || sendingRef.current) return;
    
    // 4. HARD REQUEST DEDUP
    const now = Date.now();
    if (now - lastRequestRef.current.timestamp < 500 && lastRequestRef.current.text === text) {
      console.warn("Dropped duplicate request (dedup window)");
      return;
    }
    lastRequestRef.current = { timestamp: now, text };
    
    // 1. STREAM OWNERSHIP MODEL & EXACTLY ONCE
    const nonce = crypto.randomUUID();
    const leaseId = `${currentSessionId}_${nonce}`;
    activeLeaseRef.current = leaseId;
    activeStreamsCountRef.current += 1;
    
    performance.mark('start_send');
    
    sendingRef.current = true;
    setError(null);
    setStatus("queued");
    setIsLoading(true);
    
    const userMsg = { id: Date.now(), sender: 'user', text };
    const botMsgId = Date.now() + 1;
    
    setMessages((prev) => [...prev, userMsg]);
    
    abortControllerRef.current = new AbortController();
    let accumulatedText = "";
    let hasAccepted = false;
    let activeMessageId = null;
    let activeGenerationId = null;
    
    try {
      const response = await fetch(API_CONFIG.ENDPOINTS.CHAT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: text, nonce }),
        signal: abortControllerRef.current.signal
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let lastChunk = null;

      let repeatCount = 0;

      while (true) {
        // STREAM OWNERSHIP VALIDATION
        if (activeLeaseRef.current !== leaseId) {
          console.warn(`[LEASE EXPIRED] Dropping orphan tokens for lease ${leaseId}`);
          break;
        }
        
        const { value, done } = await reader.read();
        if (done) {
          // EOF Completion state fix
          setIsLoading(false);
          setStatus('');
          setMessages((prev) => {
            const next = [...prev];
            const targetMsgId = activeMessageId || botMsgId;
            const idx = next.findIndex(m => m.id === targetMsgId);
            if (idx !== -1) next[idx] = { ...next[idx], streaming: false };
            return next;
          });
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        
        // 5. Deduplicate chunks
        const incomingChunkTrimmed = chunk.trim();
        const previousChunkTrimmed = (lastChunk || "").trim();
        
        if (incomingChunkTrimmed !== "" && incomingChunkTrimmed === previousChunkTrimmed) {
            repeatCount++;
            if (repeatCount >= 3) {
                cancel_generation();
                setStatus('completed');
                break;
            }
            continue; // Do NOT append
        } else {
            repeatCount = 0;
        }
        lastChunk = chunk;

        // Skip if assistantText already ends with this sentence chunk
        if (incomingChunkTrimmed !== "" && accumulatedText.trim().endsWith(incomingChunkTrimmed) && incomingChunkTrimmed.length > 4) {
            continue;
        }
        
        buffer += chunk;
        
        // Match brackets [[...]] while retaining them in split results
        const tokens = buffer.split(/(\[\[.*?\]\])/g);
        
        // Save incomplete bracket chunk in the buffer for the next chunk read
        buffer = tokens.pop() || "";

        for (const token of tokens) {
          if (!token) continue;
          
          if (token.startsWith("[[STATUS:accepted")) {
            hasAccepted = true;
            setStatus("executing...");
            
            const cleanToken = token.replace("[[STATUS:accepted", "").replace("]]", "");
            if (cleanToken.startsWith(":")) {
              const parts = cleanToken.substring(1).split(":");
              activeMessageId = parts[0];
              activeGenerationId = parts[1];
            } else {
              activeMessageId = botMsgId;
              activeGenerationId = nonce;
            }
            
            // Mount optimistic bubble only after backend ACK
            setMessages((prev) => [
              ...prev,
              { id: activeMessageId, sender: 'friday', text: '', streaming: true, streamLease: leaseId }
            ]);
            performance.measure('send_latency', 'start_send');
            const metrics = performance.getEntriesByName('send_latency');
            console.debug(`[Telemetry] ACK latency: ${metrics[metrics.length-1].duration.toFixed(2)}ms`);
            continue;
          }
          
          if (token === "[[STATUS:duplicate_dropped]]") {
            hasAccepted = true;
            setStatus("completed");
            setIsLoading(false);
            sendingRef.current = false;
            return;
          }
          
          if (token.startsWith("[[TOKEN:")) {
            const cleanToken = token.replace("[[TOKEN:", "").replace("]]", "");
            const parts = cleanToken.split(":");
            const tokenSessionId = parts[0];
            const tokenMessageId = parts[1];
            const tokenGenerationId = parts[2];
            const b64Token = parts.slice(3).join(":");
            
            // 4. TOKEN VALIDATION
            if (
              tokenSessionId === currentSessionId &&
              tokenMessageId === activeMessageId &&
              tokenGenerationId === activeGenerationId
            ) {
              const decodedToken = atob(b64Token);
              accumulatedText += decodedToken;
              
              const sanitizedText = sanitizeFrontText(accumulatedText);
              
              setMessages((prev) => {
                const next = [...prev];
                const idx = next.findIndex(m => m.id === activeMessageId);
                if (idx === -1) {
                  return [...prev, { id: activeMessageId, sender: 'friday', text: sanitizedText, streaming: true }];
                }
                next[idx] = { ...next[idx], text: sanitizedText };
                return next;
              });
              
              // 4. Add loop guard
              if (accumulatedText.length > 3000) {
                console.warn("MAX_ASSISTANT_CHARS exceeded. Aborting generation.");
                cancel_generation();
                break;
              }
            } else {
              console.warn(`[TOKEN_VALIDATION] Dropped mismatched token: Expected ${currentSessionId}/${activeMessageId}/${activeGenerationId}, got ${tokenSessionId}/${tokenMessageId}/${tokenGenerationId}`);
            }
            continue;
          }
          
          if (token.startsWith("[[STATUS:")) {
            const nextStatus = token.replace("[[STATUS:", "").replace("]]", "").toLowerCase();
            setStatus(nextStatus);
            
            const targetMsgId = activeMessageId || botMsgId;
            setMessages((prev) => {
              const next = [...prev];
              const idx = next.findIndex(m => m.id === targetMsgId);
              if (idx !== -1 && !next[idx].text) {
                next[idx] = { ...next[idx], text: nextStatus };
              }
              return next;
            });
          } else if (token.startsWith("[[METRICS:")) {
            try { setMetrics(JSON.parse(token.replace("[[METRICS:", "").replace("]]", ""))); } catch (e) {}
          } else {
            // Non-framed regular chunks (fallback handling)
            if (accumulatedText === "" && token) {
              accumulatedText = token;
            } else {
              accumulatedText += token;
            }
            
            const sanitizedText = sanitizeFrontText(accumulatedText);
            const targetMsgId = activeMessageId || botMsgId;
            
            setMessages((prev) => {
              const next = [...prev];
              const idx = next.findIndex(m => m.id === targetMsgId);
              if (idx === -1) {
                return [...prev, { id: targetMsgId, sender: 'friday', text: sanitizedText, streaming: true }];
              }
              next[idx] = { ...next[idx], text: sanitizedText };
              return next;
            });
            
            // 4. Add loop guard
            if (accumulatedText.length > 3000) {
              console.warn("MAX_ASSISTANT_CHARS exceeded. Aborting generation.");
              cancel_generation();
              break;
            }
          }
        }
      }

      // 5. EMPTY MESSAGE PROTECTION
      const finalCleanText = sanitizeFrontText(accumulatedText);
      const outputText = finalCleanText === "" ? "[Empty response received from backend]" : finalCleanText;
      
      const targetMsgId = activeMessageId || botMsgId;
      setMessages((prev) => prev.map(m => m.id === targetMsgId ? { ...m, text: outputText, streaming: false } : m));
    } catch (err) {
      // ADVERSARIAL FIX: Don't swallow network errors silently. Display them in the chat UI.
      if (err.name !== 'AbortError') {
        const errMsg = `System Error: ${err.message || 'Connection lost'}`;
        setError(errMsg);
        const targetMsgId = activeMessageId || botMsgId;
        setMessages((prev) => prev.map(m => m.id === targetMsgId ? { ...m, text: errMsg, streaming: false } : m));
        cancel_generation();
      }
    } finally {
      activeStreamsCountRef.current = Math.max(0, activeStreamsCountRef.current - 1);
      setIsLoading(false);
      sendingRef.current = false;
      abortControllerRef.current = null;
      setStatus('');
    }
  }, [currentSessionId, isLoading]);

  // 7. React Lifecycle Effects (placed strictly at bottom after all variables/callbacks are defined)
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('friday_session_id', currentSessionId);
    } else {
      localStorage.removeItem('friday_session_id');
    }
  }, [currentSessionId]);

  useEffect(() => {
    const handleBeforeUnload = () => {
      cancel_generation();
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [cancel_generation]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const threshold = 40;
      const distanceFromBottom = container.scrollHeight - container.clientHeight - container.scrollTop;
      setIsScrolledUp(distanceFromBottom > threshold);
      
      // Dynamic scroll position persistence for session switch
      if (currentSessionId) {
        sessionScrollOffsetsRef.current[currentSessionId] = container.scrollTop;
      }
      
      // Expand window if we hit the top
      if (container.scrollTop < 50) {
        setRenderLimit(prev => prev + 100);
      }
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [currentSessionId]);

  useEffect(() => {
    if (isLoading && !isScrolledUp) {
      scrollToBottom('auto');
    }
  }, [messages, isLoading, isScrolledUp, scrollToBottom]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);
  
  // Virtualization replaces slice(-renderLimit)
  // AssistantPage will use TanStack virtualizer directly on the full array.
  
  return {
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    semanticMemories, fetchSemanticMemories, deleteSemanticMemory,
    messages, setMessages,
    isLoading, setIsLoading, status, setStatus, metrics, setMetrics, error, sendMessage, interrupt, cancel_generation,
    chatContainerRef, chatEndRef, isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  };
}
