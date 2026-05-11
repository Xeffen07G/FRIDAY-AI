import { memo } from 'react';

function Sidebar({ 
  isOpen, 
  tab, 
  setTab, 
  sessions, 
  currentSessionId, 
  switchSession, 
  deleteSession, 
  createNewSession,
  memories,
  deleteMemory
}) {
  return (
    <div className={`${isOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-slate-900/80 backdrop-blur-md border-r border-slate-800/80 flex flex-col overflow-hidden shrink-0 z-20`}>
      <div className="p-4 flex flex-col border-b border-slate-800/80 gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold tracking-wider text-slate-400">MEMORY CORE</h2>
          {tab === 'sessions' && (
            <button onClick={createNewSession} className="p-1.5 bg-slate-800 hover:bg-blue-600/20 rounded-md text-slate-300 hover:text-blue-400 border border-slate-700 hover:border-blue-500/30 transition-all shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
          )}
        </div>
        <div className="flex bg-slate-950/50 p-1 rounded-lg">
          <button 
            onClick={() => setTab('sessions')}
            className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${tab === 'sessions' ? 'bg-slate-800 text-slate-200 shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Sessions
          </button>
          <button 
            onClick={() => setTab('memories')}
            className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${tab === 'memories' ? 'bg-slate-800 text-slate-200 shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Knowledge
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5 custom-scrollbar">
        {tab === 'sessions' ? (
          Array.isArray(sessions) && sessions.length > 0 ? (
            sessions.map(session => (
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
            ))
          ) : (
            <div className="text-center py-10">
              <p className="text-xs text-slate-500 italic">No sessions found</p>
            </div>
          )
        ) : (
          Array.isArray(memories) && memories.length > 0 ? (
            memories.map(mem => (
              <div key={mem.id} className="group relative w-full text-left p-3 rounded-lg text-xs bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-all text-slate-300">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] text-blue-400 uppercase tracking-wider">{mem.metadata?.category || 'context'}</span>
                  <button 
                    onClick={() => deleteMemory(mem.id)}
                    className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </button>
                </div>
                <p className="line-clamp-3 leading-relaxed text-slate-400">{mem.text}</p>
              </div>
            ))
          ) : (
            <div className="text-center py-10">
              <p className="text-xs text-slate-500 italic">No memories stored</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}

export default memo(Sidebar);
