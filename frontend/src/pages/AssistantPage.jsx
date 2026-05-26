import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useVirtualizer } from '@tanstack/react-virtual';
import { API_CONFIG } from '../config/api';
import { useChat } from '../hooks/useChat';
import { useVoiceWebSocket } from '../hooks/useVoiceWebSocket';
import Sidebar from '../components/Sidebar';
import MessageBubble from '../components/MessageBubble';
import ChatInput from '../components/ChatInput';
import SettingsPanel from '../components/SettingsPanel';
import EngineeringHub from '../components/EngineeringHub';
import OrbCoreV2 from '../components/OrbCoreV2';
import AmbientBackground from '../components/AmbientBackground';

export default function AssistantPage() {
  const { 
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    semanticMemories, fetchSemanticMemories, deleteSemanticMemory,
    messages, setMessages, isLoading, setIsLoading, status, setStatus, metrics, setMetrics, error, sendMessage, interrupt: chatInterrupt, cancel_generation, chatContainerRef, chatEndRef,
    isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  } = useChat();

  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false);
  const visibleMessages = isHistoryExpanded ? messages : messages.slice(-6);

  const rowVirtualizer = useVirtualizer({
    count: visibleMessages.length,
    getScrollElement: () => chatContainerRef.current,
    estimateSize: () => 100,
    overscan: 15,
  });

  // WebSocket Handlers
  const handleVoiceTranscript = useCallback((text) => {
    const userMsg = { id: Date.now(), sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
  }, [setMessages]);

  const handleVoiceToken = useCallback((token) => {
    setMessages(prev => {
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.sender === 'friday' && lastMsg.streaming) {
        const next = [...prev];
        next[next.length - 1] = { ...lastMsg, text: lastMsg.text + token };
        return next;
      } else {
        return [...prev, { id: Date.now(), sender: 'friday', text: token, streaming: true }];
      }
    });
  }, [setMessages]);

  const { 
    convState, 
    isConnected,
    isRecording, 
    micEnergy,
    partialTranscript,
    voiceError,
    startRecording, 
    stopRecording, 
    interrupt: voiceInterrupt,
    events
  } = useVoiceWebSocket(
    currentSessionId, 
    handleVoiceTranscript, 
    handleVoiceToken, 
    setMetrics,
    cancel_generation
  );

  const [sidebarTab, setSidebarTab] = useState('workspace');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [isCompact, setIsCompact] = useState(false);
  const [stableMode, setStableMode] = useState(() => localStorage.getItem('friday_stable_mode') !== 'false');

  const [projectMode, setProjectMode] = useState(() => localStorage.getItem('friday_project_mode') || 'frontend');
  const [backendStatus, setBackendStatus] = useState('running');
  const [isMinimized, setIsMinimized] = useState(() => localStorage.getItem('friday_minimized') === 'true');

  useEffect(() => {
    localStorage.setItem('friday_minimized', isMinimized ? 'true' : 'false');
  }, [isMinimized]);

  // Invisible Intelligence States
  const [trustScore, setTrustScore] = useState(() => parseFloat(localStorage.getItem('friday_trust_score') || '1.0'));
  const [isUserTyping, setIsUserTyping] = useState(false);
  const [dismissedSuggestions, setDismissedSuggestions] = useState(() => JSON.parse(localStorage.getItem('friday_dismissed_suggestions') || '[]'));
  const [microToast, setMicroToast] = useState(null);
  const [quietMode, setQuietMode] = useState(() => localStorage.getItem('friday_quiet_mode') === 'true');

  useEffect(() => {
    localStorage.setItem('friday_trust_score', trustScore.toString());
  }, [trustScore]);

  useEffect(() => {
    localStorage.setItem('friday_dismissed_suggestions', JSON.stringify(dismissedSuggestions));
  }, [dismissedSuggestions]);

  useEffect(() => {
    localStorage.setItem('friday_project_mode', projectMode);
  }, [projectMode]);

  useEffect(() => {
    localStorage.setItem('friday_quiet_mode', quietMode ? 'true' : 'false');
  }, [quietMode]);

  // Memory Safety: Keep only last 20 chat messages in render state
  useEffect(() => {
    if (messages && messages.length > 20) {
      setMessages(prev => prev.slice(prev.length - 20));
    }
  }, [messages, setMessages]);

  useEffect(() => {
    const checkBackend = () => {
      // WS + Health Sync: If WebSocket is connected, force ONLINE state immediately to override REST fetch drops
      if (isConnected) {
        setBackendStatus('running');
        return;
      }
      fetch(`${API_CONFIG.ENDPOINTS.HEALTH}`)
        .then(res => {
          if (res.ok) setBackendStatus('running');
          else setBackendStatus('unavailable');
        })
        .catch(() => setBackendStatus('unavailable'));
    };
    checkBackend();
    const interval = setInterval(checkBackend, 4000);
    return () => clearInterval(interval);
  }, [isConnected]);

  const handleScroll = useCallback(() => {
    if (chatContainerRef.current && currentSessionId) {
      localStorage.setItem(`friday_scroll_${currentSessionId}`, chatContainerRef.current.scrollTop.toString());
    }
  }, [currentSessionId, chatContainerRef]);

  // Restore scroll position
  useEffect(() => {
    if (chatContainerRef.current && currentSessionId) {
      const saved = localStorage.getItem(`friday_scroll_${currentSessionId}`);
      if (saved) {
        // Ensure restoration is applied in the next tick after DOM has hydrated/rendered the virtualized list
        setTimeout(() => {
          if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = parseFloat(saved);
          }
        }, 30);
      }
    }
  }, [currentSessionId, messages]);

  const globalInterrupt = useCallback(() => {
    chatInterrupt();
    voiceInterrupt();
  }, [chatInterrupt, voiceInterrupt]);

  useEffect(() => {
    if (sidebarTab === 'memories') {
      fetchSemanticMemories();
    }
  }, [sidebarTab, fetchSemanticMemories]);

  const getMicroSuggestions = useCallback(() => {
    // If quiet mode is active, suppress all non-critical proactive suggestions
    if (quietMode) return [];

    // If trust score is low (< 0.5), we stay completely silent! Trust Decay Protection
    if (trustScore < 0.5) return [];

    const suggestions = [];

    // 1. Backend offline (Severity: Medium)
    if (backendStatus === 'offline' && !dismissedSuggestions.includes('backend_offline')) {
      suggestions.push({
        id: 'backend_offline',
        label: 'Backend server is offline',
        actionLabel: 'Restart API',
        severity: 'medium',
        onResolve: async () => {
          setMicroToast('Restarting backend server...');
          try {
            await fetch('/api/chat/settings/stable?enabled=' + stableMode, { method: 'POST' });
            sendMessage('/restart backend');
            setTrustScore(1.0); // Reset trust score on successful fix!
            setTimeout(() => setMicroToast('✓ Backend server restarted'), 2000);
            setTimeout(() => setMicroToast(null), 4000);
          } catch (e) {
            setMicroToast('Failed to restart backend');
            setTimeout(() => setMicroToast(null), 3000);
          }
        }
      });
    }

    // 2. WebSocket disconnected (Severity: Low)
    if (!isConnected && !dismissedSuggestions.includes('ws_disconnected')) {
      suggestions.push({
        id: 'ws_disconnected',
        label: 'WebSocket event channel disconnected',
        actionLabel: 'Reconnect WebSocket',
        severity: 'low',
        onResolve: () => {
          setMicroToast('Reconnecting WebSocket...');
          sendMessage('/fix websocket');
          setTrustScore(1.0); // Reset trust score on successful fix!
          setTimeout(() => setMicroToast('✓ WebSocket connected'), 2000);
          setTimeout(() => setMicroToast(null), 4000);
        }
      });
    }

    // 3. Simulated port conflict (Severity: Low)
    if (projectMode === 'frontend' && !isConnected && !dismissedSuggestions.includes('port_conflict')) {
      suggestions.push({
        id: 'port_conflict',
        label: 'Port 5173 conflict detected',
        actionLabel: 'Kill Process',
        severity: 'low',
        onResolve: () => {
          setMicroToast('Clearing occupied ports...');
          sendMessage('/clear port');
          setTrustScore(1.0); // Reset trust score on successful fix!
          setTimeout(() => setMicroToast('✓ Port 5173 freed'), 2000);
          setTimeout(() => setMicroToast(null), 4000);
        }
      });
    }

    // Flow State Protection: If user is actively typing, suppress non-critical suggestions (medium & low)
    if (isUserTyping) {
      return suggestions.filter(s => s.severity === 'critical');
    }

    return suggestions;
  }, [quietMode, trustScore, backendStatus, isConnected, dismissedSuggestions, projectMode, stableMode, sendMessage, isUserTyping]);

  const handleDismissSuggestion = useCallback((id) => {
    setDismissedSuggestions(prev => [...prev, id]);
    // Trust Decay Protection: decrement trustScore by 0.2 down to 0.0
    setTrustScore(prev => Math.max(0.0, parseFloat((prev - 0.2).toFixed(1))));
  }, []);

  // Daily Driver UX: Focus Toggle & PTT
  useEffect(() => {
    const handleFocus = (e) => {
        if (e.detail.action === 'toggle') {
            setIsCompact(prev => !prev);
        } else if (e.detail.action === 'show') {
            setIsCompact(false);
        }
    };
    
    const handlePTT = (e) => {
        if (e.detail.state === 'pressed') startRecording();
        else if (e.detail.state === 'released') stopRecording();
    };

    window.addEventListener('friday_focus_toggle', handleFocus);
    window.addEventListener('friday_ptt', handlePTT);
    return () => {
        window.removeEventListener('friday_focus_toggle', handleFocus);
        window.removeEventListener('friday_ptt', handlePTT);
    };
  }, [startRecording, stopRecording]);

  const getAmbientStatus = useCallback(() => {
    if (backendStatus === 'unavailable' && !isConnected) return 'UNAVAILABLE';
    if (isRecording) return 'LISTENING';
    
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.sender === 'friday' && lastMsg.streaming) return 'SPEAKING';
    
    if (isLoading) return 'THINKING';
    
    if (status && (status.toLowerCase().includes('executing') || status.toLowerCase().includes('tool') || status.toLowerCase().includes('running'))) return 'WORKING';
    
    return (isConnected || backendStatus === 'running') ? 'ONLINE' : 'IDLE';
  }, [backendStatus, isConnected, isLoading, status, isRecording, messages]);

  const getOrbState = useCallback(() => {
    if (isLoading) return 'THINKING';
    if (isRecording) return 'LISTENING';
    if (status && (status.toLowerCase().includes('executing') || status.toLowerCase().includes('tool') || status.toLowerCase().includes('running'))) return 'EXECUTING';
    
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.sender === 'friday' && lastMsg.streaming) return 'STREAMING';
    
    return 'IDLE';
  }, [isLoading, isRecording, status, messages]);

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-[100] flex items-center gap-3.5 px-5 py-3 bg-[#090a0c] border border-white/[0.035] shadow-2xl rounded-full font-sans text-xs text-slate-450">
        <span className="flex items-center gap-2 select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/80"></span>
          <span className="text-slate-450 tracking-wider">workspace monitoring active</span>
        </span>
        <span className="text-slate-800">|</span>
        <button 
          onClick={() => {
            setIsMinimized(false);
            setIsSidebarOpen(true);
          }}
          className="text-blue-400 hover:text-blue-300 font-bold transition-colors cursor-pointer"
        >
          Expand ↗
        </button>
      </div>
    );
  }

  const compactStyles = isCompact ? "fixed bottom-6 right-6 w-[400px] h-[600px] z-[100] shadow-[0_0_50px_rgba(0,0,0,0.5)] border-2 border-white/[0.04]" : "flex h-screen";

  return (
    <div className="flex h-screen static-depth-bg text-slate-100 font-sans overflow-hidden selection:bg-blue-500/30 selection:text-blue-100">
      
      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen}
        tab={sidebarTab}
        setTab={setSidebarTab}
        sessions={sessions}
        currentSessionId={currentSessionId}
        switchSession={switchSession}
        deleteSession={deleteSession}
        createNewSession={createNewSession}
        memories={semanticMemories}
        deleteMemory={deleteSemanticMemory}
        projectMode={projectMode}
        setProjectMode={setProjectMode}
        backendStatus={backendStatus}
        websocketStatus={isConnected ? 'connected' : 'disconnected'}
        quietMode={quietMode}
        isUserTyping={isUserTyping}
      />

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        
        {/* Sleek minimalist header */}
        <header className="flex items-center justify-between px-8 py-5 bg-transparent border-b border-white/[0.02] backdrop-blur-[12px] z-10 shrink-0">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              className="p-1.5 text-slate-500 hover:text-slate-200 rounded-lg hover:bg-obsidian-850 transition-colors cursor-pointer"
              title="Toggle Sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <h1 className="text-[10px] font-sans font-bold tracking-widest text-slate-500 uppercase select-none">
              ENZO OS
            </h1>
          </div>
          
          <div className="flex items-center gap-5">
            {/* Real Presence Indicators Only */}
            <div className={`text-[9.5px] font-mono font-bold uppercase tracking-wider select-none ${getAmbientStatus() === 'UNAVAILABLE' ? 'text-red-400' : 'text-slate-500'}`}>
              {getAmbientStatus() === 'UNAVAILABLE' ? 'Backend unavailable' : getAmbientStatus()}
            </div>

            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="p-1 text-slate-500 hover:text-slate-250 hover:bg-obsidian-850 rounded-md transition-colors cursor-pointer"
              title="Settings"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1V15a2 2 0 0 1-2-2 2 2 0 0 1 2-2v-.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2v.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden bg-transparent relative z-0">
          
          <AmbientBackground />

          {/* Ambient Orb */}
          <motion.div 
            className="absolute inset-0 pointer-events-none flex items-center justify-center z-10"
            initial={{ y: 0, x: 0, scale: 1 }}
            animate={{ 
              y: messages.length > 0 ? '-20%' : '0%',
              x: '10vw',
              scale: messages.length > 20 ? 0.8 : 1 
            }}
            transition={{ type: 'spring', stiffness: 60, damping: 20 }}
          >
            <OrbCoreV2 state={getOrbState()} />
          </motion.div>

          {/* Chat Column */}
          <div className="flex-1 flex flex-col min-w-0 relative z-20">
            <main 
              className="flex-1 overflow-y-auto p-6 md:p-8 scroll-smooth custom-scrollbar"
              ref={chatContainerRef}
              onScroll={handleScroll}
            >
              <div className="max-w-[720px] mx-auto pb-12">
                {visibleMessages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center text-center py-40 select-none animate-in fade-in duration-300">
                    <div className="font-heading text-slate-200 text-lg font-semibold tracking-tight mb-2 select-none">Ready when you are.</div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {!isHistoryExpanded && messages.length > 4 && (
                      <div className="flex justify-end mb-8 mt-4 sticky top-0 z-50">
                        <button 
                          onClick={() => setIsHistoryExpanded(true)}
                          className="px-3 py-1.5 bg-[#0a0c10]/80 backdrop-blur-md border border-white/[0.05] rounded-full text-[10px] font-mono text-slate-400 hover:text-slate-200 hover:bg-[#101318] transition-colors"
                        >
                          ⌘ History
                        </button>
                      </div>
                    )}
                    {isHistoryExpanded && (
                      <div className="flex justify-end mb-8 mt-4 sticky top-0 z-50">
                        <button 
                          onClick={() => setIsHistoryExpanded(false)}
                          className="px-3 py-1.5 bg-[#0a0c10]/80 backdrop-blur-md border border-white/[0.05] rounded-full text-[10px] font-mono text-slate-400 hover:text-slate-200 hover:bg-[#101318] transition-colors"
                        >
                          Close History
                        </button>
                      </div>
                    )}
                    <div 
                      style={{ 
                        height: `${rowVirtualizer.getTotalSize()}px`,
                        width: '100%',
                        position: 'relative'
                      }}
                    >
                      {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                        const msg = visibleMessages[virtualRow.index];
                        const isLatest = virtualRow.index === visibleMessages.length - 1;
                        const age = visibleMessages.length - 1 - virtualRow.index;
                        const opacity = isHistoryExpanded ? 1 : (age === 0 ? 1 : 0.35);

                        return (
                          <div
                            key={virtualRow.key}
                            data-index={virtualRow.index}
                            ref={rowVirtualizer.measureElement}
                            style={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              width: '100%',
                              transform: `translateY(${virtualRow.start}px)`,
                              opacity,
                              transition: 'opacity 0.4s ease-out'
                            }}
                          >
                            <MessageBubble message={msg} isLatest={isLatest} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} className="h-px w-full" />
              </div>

              {isScrolledUp && (
                <button 
                  onClick={scrollToBottom}
                  className="absolute bottom-32 left-1/2 -translate-x-1/2 bg-slate-800/90 hover:bg-slate-700 text-slate-300 p-2 rounded-full border border-slate-700 shadow-lg backdrop-blur-sm transition-all z-10 hover:text-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
                </button>
              )}
            </main>

            <div className="shrink-0 p-6 z-30">
              <ChatInput 
                onSend={sendMessage} 
                onStop={globalInterrupt} 
                isLoading={isLoading}
                isRecording={isRecording}
                startRecording={startRecording}
                stopRecording={stopRecording}
                convState={convState}
                micEnergy={micEnergy}
                partialTranscript={partialTranscript}
                voiceError={voiceError}
                lastMessage={messages[messages.length - 1]}
                projectMode={projectMode}
                onTypingStateChange={setIsUserTyping}
              />
            </div>

             {/* Micro-Toast Notification */}
             {microToast && (
               <div className="fixed bottom-24 right-6 z-50 flex items-center gap-2.5 px-4 py-2 bg-obsidian-950/80 backdrop-blur-md border border-white/[0.035] rounded-full shadow-2xl text-[10px] font-sans font-semibold text-blue-400 animate-in fade-in slide-in-from-bottom-1 duration-200">
                 <span className="w-1.5 h-1.5 rounded-full bg-blue-500/60" />
                 {microToast}
               </div>
             )}
          </div>
        </div>
      </div>

      <SettingsPanel 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        quietMode={quietMode}
        setQuietMode={setQuietMode}
      />

    </div>
  );
}
