import EngineeringHub from '../components/EngineeringHub';

export default function AssistantPage() {
  const { 
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    semanticMemories, fetchSemanticMemories, deleteSemanticMemory,
    messages, setMessages, isLoading, setIsLoading, status, setStatus, metrics, setMetrics, error, sendMessage, interrupt: chatInterrupt, chatContainerRef, chatEndRef,
    isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  } = useChat();

  const [sidebarTab, setSidebarTab] = useState('sessions');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);

  // WebSocket Handlers
  // ... (handleVoiceTranscript, handleVoiceToken)
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
    startRecording, 
    stopRecording, 
    interrupt: voiceInterrupt,
    events
  } = useVoiceWebSocket(
    currentSessionId, 
    handleVoiceTranscript, 
    handleVoiceToken, 
    setMetrics
  );

  const globalInterrupt = useCallback(() => {
    chatInterrupt();
    voiceInterrupt();
  }, [chatInterrupt, voiceInterrupt]);

  useEffect(() => {
    if (sidebarTab === 'memories') {
      fetchSemanticMemories();
    }
  }, [sidebarTab]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden selection:bg-blue-500/30 selection:text-blue-100">
      
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
      />

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Header */}
        <header className="flex items-center gap-3 px-6 py-4 bg-slate-900/40 border-b border-slate-800/80 backdrop-blur-md z-10 shrink-0">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 -ml-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center">
              <div className={`absolute w-3.5 h-3.5 rounded-full ${error ? 'bg-red-500/20' : 'bg-emerald-500/20'} animate-ping`}></div>
              <div className={`w-2 h-2 rounded-full ${error ? 'bg-red-500 shadow-[0_0_8px_#ef4444]' : 'bg-emerald-400 shadow-[0_0_8px_#34d399]'}`}></div>
            </div>
            <h1 className="text-lg font-semibold tracking-wide text-slate-200 flex items-center gap-2">
              F.R.I.D.A.Y. <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase tracking-widest">Cognitive OS</span>
            </h1>
            
            {/* Realtime Status Indicator */}
            <div className="hidden sm:flex items-center gap-2 ml-4 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50">
              <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 animate-pulse'}`}></span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  {isConnected ? 'WS: CONNECTED' : 'WS: OFFLINE'}
              </span>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <button 
              onClick={() => setIsDiagnosticsOpen(!isDiagnosticsOpen)}
              className={`p-2 rounded-lg transition-all ${isDiagnosticsOpen ? 'text-blue-400 bg-blue-600/10' : 'text-slate-400 hover:text-blue-400 hover:bg-blue-600/10'}`}
              title="Toggle Engineering Hub"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            </button>

            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
              title="Settings"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1V15a2 2 0 0 1-2-2 2 2 0 0 1 2-2v-.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2v.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat Column */}
          <main 
            className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth custom-scrollbar relative"
            ref={chatContainerRef}
          >
            <div className="max-w-4xl mx-auto space-y-6 pb-24">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              
              {isLoading && (
                <div className="flex flex-col w-full items-start gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="glass-morphism text-slate-400 px-5 py-4 rounded-2xl rounded-bl-sm text-[15px] flex items-center gap-3 shadow-sm">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                    {status && <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest animate-pulse">{status}</span>}
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

            <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent">
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
              />
            </div>
          </main>

          {/* Engineering Panel (Side Overlay) */}
          {(isDiagnosticsOpen || sidebarTab === 'engineering') && (
            <motion.div 
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              className="w-[400px] border-l border-white/5 bg-slate-950/50 backdrop-blur-sm p-4 hidden lg:block"
            >
               <EngineeringHub 
                 events={events}
                 metrics={metrics}
                 isConnected={isConnected}
                 convState={convState}
               />
            </motion.div>
          )}
        </div>
      </div>

      <SettingsPanel isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
      {/* Mobile Diagnostics Overlay */}
      {isDiagnosticsOpen && (
        <div className="fixed inset-0 z-50 lg:hidden p-4 bg-slate-950/90 backdrop-blur-md">
           <div className="flex justify-end mb-4">
              <button onClick={() => setIsDiagnosticsOpen(false)} className="p-2 text-slate-400 hover:text-white bg-slate-800 rounded-full">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
           </div>
           <EngineeringHub 
             events={events}
             metrics={metrics}
             isConnected={isConnected}
             convState={convState}
           />
        </div>
      )}
    </div>
  );
}
