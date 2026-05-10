import { useChat } from './hooks/useChat';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';

export default function App() {
  const { 
    sessions, currentSessionId, createNewSession, switchSession, deleteSession,
    messages, isLoading, error, sendMessage, chatContainerRef, chatEndRef,
    isSidebarOpen, setIsSidebarOpen, isScrolledUp, scrollToBottom
  } = useChat();

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden selection:bg-blue-500/30 selection:text-blue-100">
      
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-slate-900/80 backdrop-blur-md border-r border-slate-800/80 flex flex-col overflow-hidden shrink-0 z-20`}>
        <div className="p-4 flex items-center justify-between border-b border-slate-800/80">
          <h2 className="text-xs font-semibold tracking-wider text-slate-400">MEMORY CORE</h2>
          <button onClick={createNewSession} className="p-1.5 bg-slate-800 hover:bg-blue-600/20 rounded-md text-slate-300 hover:text-blue-400 border border-slate-700 hover:border-blue-500/30 transition-all shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 custom-scrollbar">
          {sessions.map(session => (
            <div 
              key={session.id}
              onClick={() => switchSession(session.id)}
              className={`group flex items-center justify-between w-full text-left px-3 py-2.5 rounded-lg text-sm cursor-pointer transition-all ${
                currentSessionId === session.id 
                  ? 'bg-blue-600/10 text-blue-300 border border-blue-500/30 shadow-inner' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
              }`}
            >
              <span className="truncate flex-1 pr-2">{session.title}</span>
              <button 
                onClick={(e) => deleteSession(session.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-all"
                title="Delete Session"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          ))}
        </div>
      </div>

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
              F.R.I.D.A.Y. <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">CORE v1.0</span>
            </h1>
          </div>
          {error && <span className="ml-auto text-xs font-medium text-red-400 bg-red-400/10 px-3 py-1 rounded-full border border-red-400/20">{error}</span>}
        </header>

        {/* Main Chat Area */}
        <main 
          className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth custom-scrollbar relative"
          ref={chatContainerRef}
          onScroll={chatContainerRef.current?.handleScroll} // Handled dynamically in useChat via state tracking
        >
          <div className="max-w-4xl mx-auto space-y-6 pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            
            {/* Loading State */}
            {isLoading && messages[messages.length - 1]?.sender === 'user' && (
              <div className="flex w-full justify-start animate-pulse">
                <div className="bg-slate-800 text-slate-400 border border-slate-700/50 px-5 py-4 rounded-2xl rounded-bl-sm text-[15px] flex items-center gap-2 shadow-sm">
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            )}
            
            {/* Auto-scroll target */}
            <div ref={chatEndRef} className="h-px w-full" />
          </div>
        </main>

        {/* Jump to bottom button */}
        {isScrolledUp && (
          <button 
            onClick={scrollToBottom}
            className="absolute bottom-24 left-1/2 -translate-x-1/2 bg-slate-800/90 hover:bg-slate-700 text-slate-300 p-2 rounded-full border border-slate-700 shadow-lg backdrop-blur-sm transition-all z-10 hover:text-white"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
          </button>
        )}

        {/* Input Area */}
        <ChatInput onSend={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
