import { useState, useEffect, useCallback } from 'react';
import { useChat } from './hooks/useChat';
import { useVoiceWebSocket } from './hooks/useVoiceWebSocket';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';
import SettingsPanel from './components/SettingsPanel';
import Sidebar from './components/Sidebar';
import DiagnosticsPanel from './components/DiagnosticsPanel';
import DiagnosticsDashboard from './components/DiagnosticsDashboard';

export default function App() {
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
    interrupt: voiceInterrupt 
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
              F.R.I.D.A.Y. <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">REALTIME v2.0</span>
            </h1>
            
            {/* Realtime Status Indicator */}
            <div className="hidden sm:flex items-center gap-2 ml-4 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50">
              <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 animate-pulse'}`}></span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  {isConnected ? 'WS: CONNECTED' : 'WS: OFFLINE'}
              </span>
            </div>

            {convState !== 'idle' && (
              <div className="hidden sm:flex items-center gap-2 ml-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50">
                <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                  convState === 'listening' ? 'bg-red-500' :
                  convState === 'transcribing' ? 'bg-amber-500' :
                  convState === 'thinking' ? 'bg-blue-500' :
                  'bg-emerald-500'
                }`}></span>
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">{convState}</span>
              </div>
            )}
          </div>
          <div className="ml-auto flex items-center gap-3">
            {error && <span className="hidden md:block text-xs font-medium text-red-400 bg-red-400/10 px-3 py-1 rounded-full border border-red-400/20">{error}</span>}
            
            <button 
              onClick={() => setIsDiagnosticsOpen(true)}
              className="p-2 text-slate-400 hover:text-blue-400 hover:bg-blue-600/10 rounded-lg transition-colors"
              title="Diagnostics"
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

        {/* Main Chat Area */}
        <main 
          className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth custom-scrollbar relative"
          ref={chatContainerRef}
        >
          <div className="max-w-4xl mx-auto space-y-6 pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            
            {isLoading && (
              <div className="flex flex-col w-full items-start gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="bg-slate-800 text-slate-400 border border-slate-700/50 px-5 py-4 rounded-2xl rounded-bl-sm text-[15px] flex items-center gap-3 shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  {status && <span className="text-xs font-mono text-slate-500 uppercase tracking-widest animate-pulse">{status}</span>}
                </div>
              </div>
            )}

            {metrics && !isLoading && (
              <div className="flex justify-center">
                <div className="flex gap-4 px-4 py-2 bg-slate-900/50 border border-slate-800/80 rounded-full text-[10px] font-mono text-slate-500 flex-wrap justify-center">
                  {metrics.stt_ms && <span>STT: {metrics.stt_ms}ms</span>}
                  {metrics.retrieval_ms && <span>RET: {metrics.retrieval_ms}ms</span>}
                  {metrics.generation_ms && <span>GEN: {metrics.generation_ms}ms</span>}
                  {metrics.tts_ms && <span>TTS: {metrics.tts_ms}ms</span>}
                  {metrics.total_ms && <span className="text-blue-400/70">TOTAL: {metrics.total_ms}ms</span>}
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} className="h-px w-full" />
          </div>
        </main>

        {isScrolledUp && (
          <button 
            onClick={scrollToBottom}
            className="absolute bottom-24 left-1/2 -translate-x-1/2 bg-slate-800/90 hover:bg-slate-700 text-slate-300 p-2 rounded-full border border-slate-700 shadow-lg backdrop-blur-sm transition-all z-10 hover:text-white"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
          </button>
        )}

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

      <SettingsPanel isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
      {/* Diagnostics Telemetry Overlay */}
      {isDiagnosticsOpen && (
        <div className="fixed top-20 right-6 z-50 animate-in fade-in zoom-in duration-200">
           <DiagnosticsDashboard 
             metrics={metrics} 
             isConnected={isConnected} 
             convState={convState} 
             onClose={() => setIsDiagnosticsOpen(false)}
           />
        </div>
      )}
    </div>
  );
}
