import { useState, useRef, useEffect } from 'react';

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

  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('friday_session_id', currentSessionId);
    } else {
      localStorage.removeItem('friday_session_id');
    }
  }, [currentSessionId]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isUp = scrollHeight - scrollTop - clientHeight > 100;
    setIsScrolledUp(isUp);
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!isScrolledUp) {
      scrollToBottom();
    }
  }, [messages, isLoading]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions');
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const data = await res.json();
      const sessionArray = Array.isArray(data) ? data : [];
      setSessions(sessionArray);
      if (sessionArray.length > 0) {
        if (currentSessionId && sessionArray.find(s => s.id === currentSessionId)) {
          switchSession(currentSessionId);
        } else {
          switchSession(sessionArray[0].id);
        }
      } else {
        createNewSession();
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setSessions([]);
      setError("Failed to connect to F.R.I.D.A.Y. memory core.");
    }
  };

  const createNewSession = async () => {
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
  };

  const switchSession = async (id) => {
    setCurrentSessionId(id);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/sessions/${id}/messages`);
      const data = await res.json();
      if (data.length === 0) {
        setMessages([{ id: Date.now(), sender: 'friday', text: 'F.R.I.D.A.Y. online. Awaiting your command.' }]);
      } else {
        setMessages(data);
      }
      setTimeout(scrollToBottom, 50);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    try {
      await fetch(`http://127.0.0.1:8000/api/sessions/${id}`, { method: 'DELETE' });
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) {
        const remaining = sessions.filter(s => s.id !== id);
        if (remaining.length > 0) {
          switchSession(remaining[0].id);
        } else {
          createNewSession();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSemanticMemories = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/memories');
      const data = await res.json();
      setSemanticMemories(data);
    } catch (err) {
      console.error("Failed to fetch memories", err);
    }
  };

  const deleteSemanticMemory = async (id) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/memories/${id}`, { method: 'DELETE' });
      setSemanticMemories(prev => prev.filter(m => m.id !== id));
    } catch (err) {
      console.error("Failed to delete memory", err);
    }
  };

  const abortControllerRef = useRef(null);

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setStatus("Generation cancelled");
    }
  };

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading || !currentSessionId) return;
    
    setError(null);
    setStatus("Initializing...");
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
        
        // Split chunk into tokens (it might contain multiple status/metrics tokens)
        // We use a regex that matches both status/metrics tokens and regular text
        const tokens = chunk.split(/(\[\[.*?\]\])/g);
        
        for (const token of tokens) {
          if (!token) continue;
          
          if (token.startsWith("[[STATUS:")) {
            setStatus(token.replace("[[STATUS:", "").replace("]]", ""));
          } else if (token.startsWith("[[METRICS:")) {
            try {
              setMetrics(JSON.parse(token.replace("[[METRICS:", "").replace("]]", "")));
            } catch (e) {}
          } else {
            // It's actual message text
            fullText += token;
            
            if (isFirstChunk) {
              setMessages((prev) => [...prev, { id: botMsgId, sender: 'friday', text: token, streaming: true }]);
              isFirstChunk = false;
            } else {
              setMessages((prev) => 
                prev.map(msg => 
                  msg.id === botMsgId ? { ...msg, text: fullText } : msg
                )
              );
            }
          }
        }
      }

      // Mark message as finished
      setMessages((prev) => 
        prev.map(msg => 
          msg.id === botMsgId ? { ...msg, streaming: false } : msg
        )
      );

      if (messages.length <= 1) {
        const newTitle = text.substring(0, 30) + (text.length > 30 ? '...' : '');
        setSessions(prev => prev.map(s => 
          s.id === currentSessionId ? { ...s, title: newTitle } : s
        ));
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        console.error('Chat Error:', err);
        setError('Connection failed. Please ensure the F.R.I.D.A.Y. backend is running.');
      }
    } finally {
      setIsLoading(false);
      setStatus("");
      abortControllerRef.current = null;
    }
  };

  return {
    sessions,
    currentSessionId,
    createNewSession,
    switchSession,
    deleteSession,
    semanticMemories,
    fetchSemanticMemories,
    deleteSemanticMemory,
    messages,
    isLoading,
    status,
    metrics,
    error,
    sendMessage,
    stopGeneration,
    chatContainerRef,
    chatEndRef,
    isSidebarOpen,
    setIsSidebarOpen,
    isScrolledUp,
    scrollToBottom
  };
}
