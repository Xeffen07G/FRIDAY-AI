import { useState, useRef, useEffect, useCallback } from 'react';

export function useChat() {
  const [sessions, setSessions] = useState([]);
  const [semanticMemories, setSemanticMemories] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(() => localStorage.getItem('friday_session_id') || null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [status, setStatus] = useState("");
  const [metrics, setMetrics] = useState(null);
  
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const abortControllerRef = useRef(null);

  // Persistence of session selection
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('friday_session_id', currentSessionId);
    } else {
      localStorage.removeItem('friday_session_id');
    }
  }, [currentSessionId]);

  // Unified scroll listener
  const handleScroll = useCallback(() => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // Using a 50px buffer for stability
    const isUp = scrollHeight - scrollTop - clientHeight > 50;
    if (isUp !== isScrolledUp) {
      setIsScrolledUp(isUp);
    }
  }, [isScrolledUp]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  const scrollToBottom = useCallback((behavior = 'smooth') => {
    chatEndRef.current?.scrollIntoView({ behavior });
  }, []);

  // Automatic scrolling during generation
  useEffect(() => {
    if (!isScrolledUp && (isLoading || messages.length > 0)) {
      scrollToBottom('smooth');
    }
  }, [messages, isLoading, isScrolledUp, scrollToBottom]);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions');
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
      setSessions([]);
      setError("Failed to connect to F.R.I.D.A.Y. memory core.");
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const createNewSession = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: "New Chat" })
      });
      const data = await res.json();
      setSessions(prev => [data, ...prev]);
      setCurrentSessionId(data.id);
      setMessages([{ id: Date.now(), sender: 'friday', text: 'F.R.I.D.A.Y. online. Awaiting your command.' }]);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const switchSession = useCallback(async (id) => {
    setCurrentSessionId(id);
    setError(null);
    setMessages([]); // Clear current UI immediately for responsiveness
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/sessions/${id}/messages`);
      const data = await res.json();
      if (data.length === 0) {
        setMessages([{ id: Date.now(), sender: 'friday', text: 'F.R.I.D.A.Y. online. Awaiting your command.' }]);
      } else {
        setMessages(data);
      }
      // Use requestAnimationFrame for smoother transition after state update
      requestAnimationFrame(() => scrollToBottom('auto'));
    } catch (err) {
      console.error(err);
    }
  }, [scrollToBottom]);

  const deleteSession = useCallback(async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await fetch(`http://127.0.0.1:8000/api/sessions/${id}`, { method: 'DELETE' });
      setSessions(prev => {
        const filtered = prev.filter(s => s.id !== id);
        if (currentSessionId === id) {
          if (filtered.length > 0) setTimeout(() => switchSession(filtered[0].id), 0);
          else setTimeout(createNewSession, 0);
        }
        return filtered;
      });
    } catch (err) {
      console.error(err);
    }
  }, [currentSessionId, switchSession, createNewSession]);

  const fetchSemanticMemories = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/memories');
      const data = await res.json();
      setSemanticMemories(data);
    } catch (err) {
      console.error("Failed to fetch memories", err);
    }
  }, []);

  const deleteSemanticMemory = useCallback(async (id) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/memories/${id}`, { method: 'DELETE' });
      setSemanticMemories(prev => prev.filter(m => m.id !== id));
    } catch (err) {
      console.error("Failed to delete memory", err);
    }
  }, []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setStatus("Generation stopped");
    }
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading || !currentSessionId) return;
    
    setError(null);
    setStatus("Thinking...");
    setMetrics(null);
    
    const userMsg = { id: Date.now(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setIsScrolledUp(false);
    
    abortControllerRef.current = new AbortController();
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: text }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      const botMsgId = Date.now() + 1;
      let fullText = "";
      let isFirstChunk = true;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const tokens = chunk.split(/(\[\[.*?\]\])/g);
        
        // Process chunk tokens in batch
        let chunkStatus = null;
        let chunkMetrics = null;
        let chunkText = "";

        for (const token of tokens) {
          if (!token) continue;
          if (token.startsWith("[[STATUS:")) {
            chunkStatus = token.replace("[[STATUS:", "").replace("]]", "");
          } else if (token.startsWith("[[METRICS:")) {
            try { chunkMetrics = JSON.parse(token.replace("[[METRICS:", "").replace("]]", "")); } catch (e) {}
          } else {
            chunkText += token;
          }
        }

        // Apply batch updates
        if (chunkStatus) setStatus(chunkStatus);
        if (chunkMetrics) setMetrics(chunkMetrics);
        if (chunkText) {
          fullText += chunkText;
          setMessages((prev) => {
            if (isFirstChunk) {
              isFirstChunk = false;
              return [...prev, { id: botMsgId, sender: 'friday', text: chunkText, streaming: true }];
            }
            const next = [...prev];
            const idx = next.findIndex(m => m.id === botMsgId);
            if (idx !== -1) next[idx] = { ...next[idx], text: fullText };
            return next;
          });
        }
      }

      setMessages((prev) => prev.map(msg => 
        msg.id === botMsgId ? { ...msg, streaming: false } : msg
      ));

      // Update title if first message
      if (messages.length <= 1) {
        const newTitle = text.substring(0, 30) + (text.length > 30 ? '...' : '');
        setSessions(prev => prev.map(s => s.id === currentSessionId ? { ...s, title: newTitle } : s));
      }

    } catch (err) {
      if (err.name === 'AbortError') console.log('Stream aborted');
      else {
        console.error('Chat Error:', err);
        setError('Connection failed. Please ensure the backend is active.');
      }
    } finally {
      setIsLoading(false);
      setStatus("");
      abortControllerRef.current = null;
    }
  }, [currentSessionId, isLoading, messages.length]);

  return {
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    semanticMemories, fetchSemanticMemories, deleteSemanticMemory,
    messages, isLoading, status, metrics, error, sendMessage, stopGeneration,
    chatContainerRef, chatEndRef, isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  };
}
