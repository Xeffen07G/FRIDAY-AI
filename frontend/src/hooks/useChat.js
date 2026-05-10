import { useState, useRef, useEffect } from 'react';

export function useChat() {
  const [sessions, setSessions] = useState([]);
  const [semanticMemories, setSemanticMemories] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(() => localStorage.getItem('friday_session_id') || null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
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

  // Auto-scroll to the bottom when messages change, ONLY if not scrolled up
  useEffect(() => {
    if (!isScrolledUp) {
      scrollToBottom();
    }
  }, [messages, isLoading]);

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions');
      const data = await res.json();
      setSessions(data);
      if (data.length > 0) {
        if (currentSessionId && data.find(s => s.id === currentSessionId)) {
          switchSession(currentSessionId);
        } else {
          switchSession(data[0].id);
        }
      } else {
        createNewSession();
      }
    } catch (err) {
      console.error("Failed to load sessions", err);
      setMessages([{ id: 1, sender: 'friday', text: 'F.R.I.D.A.Y. offline mode.' }]);
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
      setTimeout(scrollToBottom, 50); // Small delay to ensure render
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

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading || !currentSessionId) return;
    
    setError(null);
    const userMsg = { id: Date.now(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setIsScrolledUp(false); // Force scroll down on send
    setTimeout(scrollToBottom, 10);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: text }),
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      const botMsgId = Date.now() + 1;
      let isFirstChunk = true;
      let done = false;

      // Watchdog timer to prevent frontend hang if backend dies without closing
      let streamTimeout;
      const resetStreamTimeout = () => {
        clearTimeout(streamTimeout);
        streamTimeout = setTimeout(() => {
          console.error("Stream reader timeout - no chunks received for 15s");
          setMessages((prev) => 
            prev.map(msg => 
              msg.id === botMsgId ? { ...msg, text: msg.text + "\n\n⚠️ Stream connection lost." } : msg
            )
          );
          setIsLoading(false);
        }, 15000);
      };

      try {
        resetStreamTimeout();
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          resetStreamTimeout();
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            
            if (isFirstChunk) {
              setMessages((prev) => [...prev, { id: botMsgId, sender: 'friday', text: chunk }]);
              isFirstChunk = false;
            } else {
              setMessages((prev) => 
                prev.map(msg => 
                  msg.id === botMsgId ? { ...msg, text: msg.text + chunk } : msg
                )
              );
            }
          }
        }
        clearTimeout(streamTimeout);
      } catch (streamErr) {
        clearTimeout(streamTimeout);
        throw streamErr;
      }

      // Update session title locally if it was the first message
      if (messages.length <= 1) {
        const newTitle = text.substring(0, 30) + (text.length > 30 ? '...' : '');
        setSessions(prev => prev.map(s => 
          s.id === currentSessionId ? { ...s, title: newTitle } : s
        ));
      }

    } catch (err) {
      console.error('Chat Error:', err);
      setError('Connection failed. Please ensure the F.R.I.D.A.Y. backend is running.');
      setMessages((prev) => [...prev, { 
        id: Date.now() + 1, 
        sender: 'friday', 
        text: 'Error: Could not reach the core systems.' 
      }]);
    } finally {
      setIsLoading(false);
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
    error,
    sendMessage,
    chatContainerRef,
    chatEndRef,
    isSidebarOpen,
    setIsSidebarOpen,
    isScrolledUp,
    scrollToBottom
  };
}
