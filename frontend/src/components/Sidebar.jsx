import { memo, useState } from 'react';

const MODES = [
  { id: 'frontend', name: 'Frontend', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { id: 'backend', name: 'Backend', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { id: 'debug', name: 'Debug', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
  { id: 'research', name: 'Research', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  { id: 'git', name: 'Git Recovery', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
];

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
  deleteMemory,
  projectMode = 'frontend',
  setProjectMode,
  backendStatus = 'running',
  websocketStatus = 'connected',
  onSendAction,
  quietMode = false,
  isUserTyping = false
}) {
  const getModeStyle = (modeId) => {
    const isSelected = projectMode === modeId;
    return isSelected 
      ? 'bg-obsidian-800 border-white/[0.04] text-slate-100 shadow-sm' 
      : 'text-slate-500 hover:text-slate-350 hover:bg-obsidian-900/20 border-transparent';
  };

  return (
    <div className={`${isOpen ? 'w-76' : 'w-0'} transition-sidebar bg-[#090a0c]/84 border-r border-white/[0.03] flex flex-col overflow-hidden shrink-0 z-20 ${isUserTyping ? 'focus-guided-inactive' : 'focus-guided-active'}`}>
      
      {/* Sidebar Header Tab Selector */}
      <div className="px-6 py-5 flex flex-col border-b border-white/[0.025] gap-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5 select-none">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              <h2 className="text-[12px] font-heading font-bold tracking-widest text-slate-200 uppercase">ENZO</h2>
            </div>
            <span className="text-[9px] font-sans text-slate-500 pl-3.5 uppercase tracking-wide">Ambient Intelligence</span>
          </div>
        </div>
        <div className="flex bg-obsidian-950 p-0.5 rounded-lg border border-white/[0.02]">
          <button 
            onClick={() => setTab('workspace')}
            className={`flex-1 text-[10px] font-sans font-semibold py-1.5 rounded-md transition-premium press-tactile ${tab === 'workspace' ? 'bg-obsidian-800 text-slate-100 border border-white/[0.03] shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Focus
          </button>
          <button 
            onClick={() => setTab('sessions')}
            className={`flex-1 text-[10px] font-sans font-semibold py-1.5 rounded-md transition-premium press-tactile ${tab === 'sessions' ? 'bg-obsidian-800 text-slate-100 border border-white/[0.03] shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Chats
          </button>
          <button 
            onClick={() => setTab('memories')}
            className={`flex-1 text-[10px] font-sans font-semibold py-1.5 rounded-md transition-premium press-tactile ${tab === 'memories' ? 'bg-obsidian-800 text-slate-100 border border-white/[0.03] shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Workspace
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {tab === 'workspace' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            
            {/* Project Focus Modes */}
            <div className="space-y-2.5">
              <span className="text-[9px] font-bold tracking-wider font-sans text-slate-500 uppercase select-none">WORKSPACE FOCUS</span>
              <div className="grid grid-cols-1 gap-1.5">
                {MODES.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setProjectMode(m.id)}
                    className={`px-3 py-2.5 text-xs font-sans font-medium rounded-lg border transition-premium press-tactile flex items-center gap-2.5 ${getModeStyle(m.id)}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${m.id === 'frontend' ? 'bg-blue-500/80' : m.id === 'backend' ? 'bg-emerald-500/80' : m.id === 'debug' ? 'bg-red-500/80' : m.id === 'research' ? 'bg-purple-500/80' : 'bg-amber-500/80'}`} />
                    {m.name}
                  </button>
                ))}
              </div>
            </div>
            
          </div>
        )}

        {tab === 'sessions' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold tracking-wider font-sans text-slate-500 uppercase select-none">CHAT HISTORY</span>
              <button 
                onClick={createNewSession} 
                className="px-2.5 py-1 bg-obsidian-950 border border-white/[0.02] hover:bg-obsidian-800 rounded-md text-[10px] font-sans font-semibold text-slate-400 hover:text-slate-200 transition-premium press-tactile flex items-center gap-1 shadow-sm"
              >
                <span>+</span> New Chat
              </button>
            </div>
            <div className="space-y-1">
              {Array.isArray(sessions) && sessions.length > 0 ? (
                sessions.map(session => (
                  <div 
                    key={session.id}
                    onClick={() => switchSession(session.id)}
                    className={`group flex items-center justify-between w-full text-left px-3.5 py-3 rounded-xl text-[13px] font-sans cursor-pointer transition-premium ${
                      currentSessionId === session.id 
                        ? 'bg-obsidian-850 text-slate-100 border border-white/[0.03] shadow-sm font-medium' 
                        : 'text-slate-500 hover:bg-obsidian-950/30 hover:text-slate-350 border border-transparent'
                    }`}
                  >
                    <span className="truncate flex-1 pr-2">{session.title}</span>
                    <button 
                      onClick={(e) => deleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-650 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors"
                      title="Delete Session"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                  </div>
                ))
              ) : (
                <div className="text-center py-10">
                  <p className="text-xs text-slate-600 italic font-sans">No chats found</p>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === 'memories' && (
          <div className="space-y-4">
            <span className="text-[9px] font-bold tracking-wider font-sans text-slate-500 uppercase select-none">WORKSPACE CONTINUITY</span>
            <div className="space-y-3">
              {Array.isArray(memories) && memories.length > 0 ? (
                memories.map((ws, i) => (
                  <div key={i} className="group relative w-full text-left p-4 rounded-xl bg-obsidian-950/20 border border-white/[0.025] hover:border-white/[0.04] transition-premium text-slate-400 font-sans">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-slate-200 tracking-tight">{ws.project_name}</span>
                      {ws.git_branch && (
                        <span className="text-[8.5px] text-blue-400/90 uppercase tracking-widest font-bold font-mono bg-blue-500/[0.04] border border-blue-500/10 px-1.5 py-0.5 rounded-md">
                          {ws.git_branch}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-[9.5px] font-mono text-slate-600 truncate mb-3" title={ws.project_path}>
                      {ws.project_path}
                    </p>

                    {ws.recent_files && ws.recent_files.length > 0 && (
                      <div className="mb-3 space-y-1">
                        <span className="text-[8px] font-bold tracking-widest text-slate-550 uppercase">Recent Files</span>
                        <div className="flex flex-wrap gap-1">
                          {ws.recent_files.slice(0, 3).map((file, fIdx) => (
                            <span key={fIdx} className="text-[9.5px] font-mono text-slate-450 bg-obsidian-900 border border-white/[0.015] px-1.5 py-0.5 rounded truncate max-w-[120px]">
                              {file.split('/').pop().split('\\').pop()}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {ws.terminal_history && ws.terminal_history.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[8px] font-bold tracking-widest text-slate-550 uppercase">Recent Commands</span>
                        <div className="bg-obsidian-950 border border-white/[0.015] p-2 rounded-lg font-mono text-[10px] text-slate-500 space-y-0.5 select-all">
                          {ws.terminal_history.slice(0, 2).map((cmd, cIdx) => (
                            <div key={cIdx} className="truncate">
                              <span className="text-slate-650 mr-1.5">$</span>{cmd}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-10">
                  <p className="text-xs text-slate-600 italic font-sans">No workspace logs found</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(Sidebar);
