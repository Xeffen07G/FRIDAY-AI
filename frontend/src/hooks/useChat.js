import { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

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

  const scrollToBottom = useCallback((behavior = 'smooth') => {
    chatEndRef.current?.scrollIntoView({ behavior });
  }, []);

  const fetchSessions = useCallback(async () => {
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
      setError("Failed to connect to F.R.I.D.A.Y. memory core.");
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

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
      setMessages([{ id: Date.now(), sender: 'friday', text: 'F.R.I.D.A.Y. online. Awaiting your command.' }]);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const switchSession = useCallback(async (id) => {
    setCurrentSessionId(id);
    setError(null);
    setMessages([]);
    try {
      const res = await fetch(`${API_CONFIG.ENDPOINTS.SESSIONS}/${id}/messages`);
      const data = await res.json();
      if (data.length === 0) {
        setMessages([{ id: Date.now(), sender: 'friday', text: 'F.R.I.D.A.Y. online. Awaiting your command.' }]);
      } else {
        setMessages(data);
      }
      requestAnimationFrame(() => scrollToBottom('auto'));
    } catch (err) {
      console.error(err);
    }
  }, [scrollToBottom]);

  const deleteSession = useCallback(async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await fetch(`${API_CONFIG.ENDPOINTS.SESSIONS}/${id}`, { method: 'DELETE' });
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
      const res = await fetch(API_CONFIG.ENDPOINTS.MEMORIES);
      const data = await res.json();
      setSemanticMemories(data);
    } catch (err) {
      console.error("Failed to fetch memories", err);
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

  const interrupt = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setStatus('');
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading || !currentSessionId) return;
    
    setError(null);
    setStatus("Thinking...");
    setIsLoading(true);
    
    const userMsg = { id: Date.now(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    
    abortControllerRef.current = new AbortController();
    let accumulatedText = "";
    const botMsgId = Date.now() + 1;

    try {
      const response = await fetch(API_CONFIG.ENDPOINTS.CHAT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: text }),
        signal: abortControllerRef.current.signal
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const tokens = chunk.split(/(\[\[.*?\]\])/g);

        for (const token of tokens) {
          if (!token) continue;
          if (token.startsWith("[[STATUS:")) {
            setStatus(token.replace("[[STATUS:", "").replace("]]", ""));
          } else if (token.startsWith("[[METRICS:")) {
            try { setMetrics(JSON.parse(token.replace("[[METRICS:", "").replace("]]", ""))); } catch (e) {}
          } else {
            accumulatedText += token;
            setMessages((prev) => {
              const next = [...prev];
              const idx = next.findIndex(m => m.id === botMsgId);
              if (idx === -1) {
                return [...prev, { id: botMsgId, sender: 'friday', text: accumulatedText, streaming: true }];
              }
              next[idx] = { ...next[idx], text: accumulatedText };
              return next;
            });
          }
        }
      }

      setMessages((prev) => prev.map(m => m.id === botMsgId ? { ...m, streaming: false } : m));
    } catch (err) {
      if (err.name !== 'AbortError') setError("F.R.I.D.A.Y. communication link broken.");
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
      setStatus('');
    }
  }, [currentSessionId, isLoading]);

  return {
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    semanticMemories, fetchSemanticMemories, deleteSemanticMemory,
    messages, setMessages, isLoading, setIsLoading, status, setStatus, metrics, setMetrics, error, sendMessage, interrupt,
    chatContainerRef, chatEndRef, isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  };
}
