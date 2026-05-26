import { useState, useRef, useEffect } from 'react';

export default function ChatInput({ 
  onSend, 
  onStop, 
  isLoading, 
  isRecording, 
  startRecording, 
  stopRecording, 
  convState,
  micEnergy = 0,
  partialTranscript = '',
  voiceError = null,
  lastMessage = null,
  projectMode = 'frontend',
  onTypingStateChange
}) {
  const [inputValue, setInputValue] = useState('');
  const [showPalette, setShowPalette] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isCompressing, setIsCompressing] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const fileInputRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    };
  }, []);

  const getCommands = () => {
    switch (projectMode) {
      case 'frontend':
        return [
          { name: '/resume frontend', desc: 'Restore frontend stack & opening browser', type: 'workflow', shortcut: '⌥R' },
          { name: '/start vite', desc: 'Run Vite dev server on port 5173', type: 'action', shortcut: '⌥V' },
          { name: '/check ports', desc: 'Verify Port 5173 & 8000 occupancy', type: 'diagnostic', shortcut: '⌥P' },
          { name: '/open browser', desc: 'Reopen dev address in chrome browser', type: 'action', shortcut: '⌥B' },
          { name: '/open vscode', desc: 'Quick launch VSCode workspace editor', type: 'action', shortcut: '⌥O' },
        ];
      case 'backend':
        return [
          { name: '/restart backend', desc: 'Restart core API server on port 8000', type: 'action', shortcut: '⌥B' },
          { name: '/db status', desc: 'Inspect database pools & normalization', type: 'diagnostic', shortcut: '⌥D' },
          { name: '/check ports', desc: 'Verify Port 8000 & 5173 occupancy', type: 'diagnostic', shortcut: '⌥P' },
          { name: '/docs api', desc: 'Launch browser to Swagger FastAPI /docs', type: 'action', shortcut: '⌥A' },
          { name: '/tail logs', desc: 'Read active background uvicorn output logs', type: 'action', shortcut: '⌥L' },
        ];
      case 'debug':
        return [
          { name: '/fix websocket', desc: 'Reconnect active live event channels', type: 'diagnostic', shortcut: '⌥F' },
          { name: '/clear port', desc: 'Clear occupied processes on Port 8000', type: 'action', shortcut: '⌥C' },
          { name: '/check ram', desc: 'Inspect system RAM usage statistics', type: 'diagnostic', shortcut: '⌥R' },
          { name: '/diagnose', desc: 'Execute diagnostic health panel checks', type: 'diagnostic', shortcut: '⌥D' },
          { name: '/stable', desc: 'Toggle production lockdown safety state', type: 'setting', shortcut: '⌥S' },
        ];
      case 'research':
        return [
          { name: '/read design', desc: 'Display core active DESIGN.md architecture', type: 'action', shortcut: '⌥R' },
          { name: '/audit schemas', desc: 'Verify Pydantic model configurations', type: 'diagnostic', shortcut: '⌥A' },
          { name: '/query core', desc: 'Retrieve matching semantic memories', type: 'action', shortcut: '⌥Q' },
          { name: '/scan files', desc: 'Map workspace filesystem module count', type: 'diagnostic', shortcut: '⌥S' },
          { name: '/performance', desc: 'Toggle high-performance engine mode', type: 'setting', shortcut: '⌥P' },
        ];
      case 'git':
        return [
          { name: '/git status', desc: 'Display active local file modifications', type: 'diagnostic', shortcut: '⌥S' },
          { name: '/git discard', desc: 'Safely discard local uncommitted code diffs', type: 'action', shortcut: '⌥D' },
          { name: '/git branches', desc: 'List active and tracked git branch indices', type: 'diagnostic', shortcut: '⌥B' },
          { name: '/git sync', desc: 'Fetch and pull remote tracking repositories', type: 'action', shortcut: '⌥Y' },
          { name: '/git conflicts', desc: 'Scan workspace for merge conflict annotations', type: 'diagnostic', shortcut: '⌥C' },
        ];
      default:
        return [];
    }
  };

  const getQuickActions = () => {
    switch (projectMode) {
      case 'frontend':
        return [
          { name: 'Resume Frontend', cmd: '/resume frontend', icon: '⚡', priority: 'primary' },
          { name: 'Start Vite', cmd: '/start vite', icon: '📦', priority: 'secondary' },
          { name: 'Check Ports', cmd: '/check ports', icon: '🔍', priority: 'secondary' },
          { name: 'Open Browser', cmd: '/open browser', icon: '🌐', priority: 'tertiary' },
        ];
      case 'backend':
        return [
          { name: 'Restart Backend', cmd: '/restart backend', icon: '🔌', priority: 'primary' },
          { name: 'Tail Logs', cmd: '/tail logs', icon: '📋', priority: 'secondary' },
          { name: 'API Docs', cmd: '/docs api', icon: '📖', priority: 'secondary' },
          { name: 'Check DB', cmd: '/db status', icon: '🗄️', priority: 'tertiary' },
        ];
      case 'debug':
        return [
          { name: 'Diagnose Stack', cmd: '/diagnose', icon: '⚙️', priority: 'primary' },
          { name: 'Fix Websocket', cmd: '/fix websocket', icon: '🛠️', priority: 'secondary' },
          { name: 'Clear Port 8000', cmd: '/clear port', icon: '🧹', priority: 'secondary' },
          { name: 'Stable Mode', cmd: '/stable', icon: '🔒', priority: 'tertiary' },
        ];
      case 'research':
        return [
          { name: 'Query Core', cmd: '/query core', icon: '🧠', priority: 'primary' },
          { name: 'Read DESIGN.md', cmd: '/read design', icon: '📄', priority: 'secondary' },
          { name: 'Scan Files', cmd: '/scan files', icon: '🔍', priority: 'secondary' },
          { name: 'Audit Schemas', cmd: '/audit schemas', icon: '🛡️', priority: 'tertiary' },
        ];
      case 'git':
        return [
          { name: 'Git Status', cmd: '/git status', icon: '🌱', priority: 'primary' },
          { name: 'Sync Code', cmd: '/git sync', icon: '🔄', priority: 'secondary' },
          { name: 'Branches', cmd: '/git branches', icon: '🌿', priority: 'secondary' },
          { name: 'Discard Changes', cmd: '/git discard', icon: '🗑️', priority: 'tertiary' },
        ];
      default:
        return [];
    }
  };

  const [commandHistory, setCommandHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('friday_command_history') || '[]');
    } catch {
      return [];
    }
  });

  const trackCommandExecution = (cmdName) => {
    setCommandHistory(prev => {
      const next = [cmdName, ...prev.filter(c => c !== cmdName)].slice(0, 5);
      localStorage.setItem('friday_command_history', JSON.stringify(next));
      return next;
    });
  };

  const fuzzyMatch = (text, query) => {
    if (!query) return { matches: true, score: 1.0 };
    const textLower = text.toLowerCase();
    const queryLower = query.toLowerCase();
    
    if (textLower === queryLower) return { matches: true, score: 10.0 };
    if (textLower.startsWith(queryLower)) return { matches: true, score: 5.0 };
    
    let score = 0;
    let queryIdx = 0;
    for (let i = 0; i < textLower.length; i++) {
      if (textLower[i] === queryLower[queryIdx]) {
        score += 1.0;
        if (i > 0 && textLower[i-1] === queryLower[queryIdx-1]) {
          score += 1.5;
        }
        if (i === 0 || textLower[i-1] === ' ' || textLower[i-1] === '/') {
          score += 2.0;
        }
        queryIdx++;
        if (queryIdx === queryLower.length) {
          return { matches: true, score: score / textLower.length };
        }
      }
    }
    return { matches: false, score: 0 };
  };

  const currentCommands = getCommands();
  
  const getFilteredCommands = () => {
    if (!inputValue) {
      return [...currentCommands].sort((a, b) => {
        const aIdx = commandHistory.indexOf(a.name);
        const bIdx = commandHistory.indexOf(b.name);
        if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
        if (aIdx !== -1) return -1;
        if (bIdx !== -1) return 1;
        return 0;
      });
    }
    
    const query = inputValue.startsWith('/') ? inputValue : '/' + inputValue;
    
    return currentCommands
      .map(cmd => {
        const match = fuzzyMatch(cmd.name, query);
        const descMatch = fuzzyMatch(cmd.desc, query);
        const bestScore = Math.max(match.score, descMatch.score * 0.8);
        const matches = match.matches || descMatch.matches;
        return { ...cmd, score: bestScore, matches };
      })
      .filter(cmd => cmd.matches)
      .sort((a, b) => {
        if (b.score === a.score) {
          const aIdx = commandHistory.indexOf(a.name);
          const bIdx = commandHistory.indexOf(b.name);
          if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
          if (aIdx !== -1) return -1;
          if (bIdx !== -1) return 1;
          return 0;
        }
        return b.score - a.score;
      });
  };

  const filteredItems = getFilteredCommands();

  useEffect(() => {
    const handleGlobalKeys = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setShowPalette(prev => !prev);
        setActiveIndex(0);
      } else if (e.key === 'Escape') {
        if (isLoading && onStop) {
          e.preventDefault();
          onStop();
        } else if (showPalette) {
          e.preventDefault();
          setShowPalette(false);
        }
      }
    };
    window.addEventListener('keydown', handleGlobalKeys);
    return () => window.removeEventListener('keydown', handleGlobalKeys);
  }, [isLoading, showPalette, onStop]);

  const getContextualSuggestions = () => {
    if (!lastMessage || lastMessage.sender !== 'friday') return [];
    const text = lastMessage.text.toLowerCase();
    const suggestions = [];
    
    if (text.includes('backend server restarted') || text.includes('port 8000') || text.includes('starting core backend')) {
      suggestions.push({ label: 'Run Frontend', cmd: '/resume frontend' });
      suggestions.push({ label: 'Check Ports', cmd: '/check ports' });
    } else if (text.includes('vscode') || text.includes('vs code')) {
      suggestions.push({ label: 'Start Workspace', cmd: '/start workspace' });
      suggestions.push({ label: 'Check Ports', cmd: '/check ports' });
    } else if (text.includes('workspace restored') || text.includes('workspace setup')) {
      suggestions.push({ label: 'Check Ports', cmd: '/check ports' });
    }
    return suggestions;
  };

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
      if (onTypingStateChange) onTypingStateChange(false);
      setIsCompressing(true);
      setTimeout(() => setIsCompressing(false), 240);
      onSend(inputValue.trim());
      setInputValue('');
      setShowPalette(false);
    }
  };

  const handleStop = () => {
    if (onStop) onStop();
  };

  const selectItem = (item) => {
    if (!item) return;
    if (onTypingStateChange) onTypingStateChange(false);
    trackCommandExecution(item.name);
    if (item.name === '/stable') {
      fetch('/api/chat/settings/stable?enabled=true', { method: 'POST' }).catch(() => {});
    } else if (item.name === '/performance') {
      fetch('/api/chat/settings/performance?enabled=true', { method: 'POST' }).catch(() => {});
    }
    onSend(item.name);
    setInputValue('');
    setShowPalette(false);
  };

  const handleKeyDown = (e) => {
    if (showPalette && filteredItems.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex(prev => (prev + 1) % filteredItems.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex(prev => (prev - 1 + filteredItems.length) % filteredItems.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        selectItem(filteredItems[activeIndex]);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowPalette(false);
      }
    } else {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInputValue(val);
    if (onTypingStateChange) onTypingStateChange(true);
    
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      if (onTypingStateChange) onTypingStateChange(false);
    }, 3000);

    if (val.startsWith('/')) {
      setShowPalette(true);
      setActiveIndex(0);
    } else {
      setShowPalette(false);
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log("Selected file:", file.name);
    }
  };

  const getMicButtonStyle = () => {
    switch (convState) {
      case 'listening':
        return 'bg-red-500/10 border-red-500/20 text-red-450 shadow-sm';
      case 'transcribing':
        return 'bg-amber-500/10 border-amber-500/20 text-amber-400';
      case 'thinking':
        return 'bg-blue-500/10 border-blue-500/20 text-blue-400 animate-soft-pulse';
      case 'speaking':
        return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-450';
      default:
        return 'bg-obsidian-950 border-white/[0.025] text-slate-500 hover:text-slate-300 hover:border-white/[0.05]';
    }
  };

  return (
    <div className="py-5 px-6 relative z-20 bg-transparent transition-premium">
      
      {/* Command Palette Dropdown Overlay */}
      {showPalette && filteredItems.length > 0 && (
        <div className="absolute bottom-full mb-4 left-6 right-6 max-w-4xl mx-auto bg-obsidian-900/95 backdrop-blur-[24px] border border-white/[0.045] rounded-2xl shadow-2xl overflow-hidden z-30 divide-y divide-white/[0.02]">
          <div className="px-5 py-3 bg-obsidian-950/40 flex justify-between items-center select-none">
            <div className="flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-slate-550" />
              <span className="text-[9px] font-sans font-bold tracking-wider text-slate-500 uppercase">COMMAND PALETTE</span>
            </div>
            <span className="text-[9px] text-slate-500 font-sans">Use ↑↓ and Enter • Press Esc to close</span>
          </div>
          <div className="max-h-[220px] overflow-y-auto p-2 space-y-0.5 custom-scrollbar bg-obsidian-900/50">
            {filteredItems.map((item, idx) => (
              <div 
                key={item.name}
                onClick={() => selectItem(item)}
                onMouseEnter={() => setActiveIndex(idx)}
                className={`group flex items-center justify-between px-4 py-2.5 rounded-xl cursor-pointer transition-premium ${
                  idx === activeIndex 
                    ? 'bg-obsidian-800 text-slate-100 border border-white/[0.03] shadow-sm' 
                    : 'text-slate-500 hover:text-slate-350 hover:bg-obsidian-950/20 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <span className="text-xs opacity-60">
                    {item.type === 'workflow' ? '⚡' : item.type === 'diagnostic' ? '🔍' : item.type === 'setting' ? '⚙️' : '💻'}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-xs font-mono font-semibold tracking-wide text-slate-200">{item.name}</span>
                    <span className="text-[10px] font-sans text-slate-500">{item.desc}</span>
                  </div>
                </div>
                {item.shortcut && (
                  <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-obsidian-950 text-slate-550 border border-white/[0.02] group-hover:border-white/[0.04] transition-premium">
                    {item.shortcut}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="max-w-3xl mx-auto flex items-center gap-3">
        {/* Command Dock */}
        <div className={`flex-1 relative flex flex-col shadow-[0_16px_40px_rgba(0,0,0,0.6)] rounded-2xl overflow-hidden bg-[#0a0c10]/80 backdrop-blur-[28px] border border-white/[0.05] focus-within:border-white/[0.1] focus-within:bg-[#0d1015]/90 transition-all duration-[400ms] ease-out-calm ${isCompressing ? 'scale-[0.99] opacity-90' : 'scale-100 opacity-100'}`}>
          
          <div className="flex items-center h-[60px] px-2 relative z-10">
            {/* Mic Button - Left aligned in dock */}
            <div className="flex items-center relative">
              <button 
                onClick={toggleMic}
                className={`p-2.5 ml-1 rounded-xl transition-premium press-tactile shrink-0 z-10 relative ${getMicButtonStyle()}`}
                title={isRecording ? "Stop Listening" : "Voice Command"}
              >
                {convState === 'transcribing' ? (
                   <svg className="animate-spin text-amber-400" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
                ) : (
                  <svg className={isRecording ? "text-red-450" : "text-slate-400"} xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                  </svg>
                )}
              </button>

              {isRecording && (
                <div className="flex items-center gap-[3px] ml-3 mr-1 pointer-events-none transition-all duration-300 w-[24px]">
                  {[...Array(5)].map((_, i) => (
                    <div 
                      key={i}
                      className="w-[3px] bg-red-400 rounded-full"
                      style={{ 
                        height: `${Math.max(4, (micEnergy / 255) * 20)}px`,
                        transition: 'height 0.1s ease'
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
            
            <input
              type="text"
              ref={inputRef}
              className={`flex-1 bg-transparent py-4 px-4 focus:outline-none transition-opacity font-sans font-medium text-[15px] tracking-wide caret-blue-500 ${voiceError ? 'text-red-400 placeholder-red-400/80' : 'text-slate-100 placeholder-slate-400'} ${isRecording ? 'opacity-80' : 'opacity-100'}`}
              placeholder={voiceError ? voiceError : (isRecording ? (partialTranscript || "Listening...") : (isFocused ? "> _" : "Ask ENZO"))}
              value={isRecording ? partialTranscript : inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              readOnly={isRecording}
              onFocus={() => {
                setIsFocused(true);
                if (onTypingStateChange) onTypingStateChange(true);
              }}
              onBlur={() => {
                setIsFocused(false);
                setTimeout(() => {
                  if (onTypingStateChange) onTypingStateChange(false);
                }, 400);
              }}
            />
            
            <div className="pr-1 flex items-center">
              {isLoading ? (
                <button 
                  onClick={handleStop}
                  className="p-2.5 bg-[#0a0c10] hover:bg-[#1a1d24] text-red-400 rounded-xl transition-premium press-tactile border border-white/[0.05] shadow-sm"
                  title="Stop Generation"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="6" y="6" width="12" height="12"></rect>
                  </svg>
                </button>
              ) : (
                <button 
                  onClick={handleSend}
                  disabled={!inputValue.trim()}
                  className={`p-2.5 rounded-xl transition-premium press-tactile shadow-sm ${
                    inputValue.trim()
                      ? 'bg-slate-200 text-slate-900 hover:bg-white' 
                      : 'bg-[#101318] text-slate-600 cursor-not-allowed border border-transparent'
                  }`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Expanded Suggestions Dock */}
          <div className={`overflow-hidden transition-all duration-[400ms] ease-out-calm ${isFocused && !isRecording && !inputValue ? 'max-h-[50px] opacity-100 pb-3' : 'max-h-0 opacity-0'}`}>
            <div className="flex items-center gap-3 px-14">
               {['Search', 'Build', 'Explain', 'Continue'].map(sugg => (
                 <button 
                   key={sugg}
                   onClick={() => { setInputValue(sugg); inputRef.current?.focus(); }}
                   className="text-[11px] font-sans font-medium text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg hover:bg-white/[0.04] transition-colors border border-transparent hover:border-white/[0.05]"
                 >
                   {sugg}
                 </button>
               ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
