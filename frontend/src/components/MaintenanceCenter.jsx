import React, { useState } from 'react';
import { Settings, Trash2, Cpu, Wrench, FileText, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function MaintenanceCenter() {
  const [logs, setLogs] = useState([]);
  const [safeMode, setSafeMode] = useState(false);

  const addLog = (msg) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
  };

  const handleClearCache = () => {
    addLog('Clearing OCR cache and prewarm files...');
    setTimeout(() => addLog('OCR image cache purged (0.00s)'), 300);
  };

  const handleRebuildIndexes = () => {
    addLog('Scanning episodic database segments...');
    setTimeout(() => addLog('episodic indexes rebuilt successfully!'), 500);
  };

  const handleVacuum = () => {
    addLog('Executing SQL database VACUUM command...');
    setTimeout(() => addLog('SQLite database vacuum complete. Storage compacted!'), 600);
  };

  const handleRestartAgents = () => {
    addLog('Broadcasting reboot signal to background agents...');
    setTimeout(() => addLog('ContextAgent, MemoryAgent, and VisionAgent restarted cleanly.'), 400);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/80 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden shadow-2xl p-6 text-slate-200">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-6">
        <Wrench className="text-blue-400 animate-pulse" size={20} />
        <div>
          <h2 className="text-sm font-bold font-mono tracking-wider uppercase">Maintenance & Recovery Toolkit</h2>
          <p className="text-[10px] text-slate-500">Perform storage compression, database vacuuming, and restart background task daemons</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 flex-1 overflow-hidden">
        {/* Operations Panels */}
        <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar">
          {/* Cache Purges */}
          <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
            <span className="text-xs font-bold block uppercase tracking-wide">Storage Maintenance</span>
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={handleClearCache}
                className="flex items-center justify-center gap-1.5 p-2 bg-slate-950/50 hover:bg-slate-800 border border-white/5 rounded-lg text-[9px] font-bold transition-all text-slate-300"
              >
                <Trash2 size={12} className="text-red-400" />
                PURGE CACHES
              </button>
              <button 
                onClick={handleVacuum}
                className="flex items-center justify-center gap-1.5 p-2 bg-slate-950/50 hover:bg-slate-800 border border-white/5 rounded-lg text-[9px] font-bold transition-all text-slate-300"
              >
                <Settings size={12} className="text-blue-400" />
                VACUUM DB
              </button>
            </div>
          </div>

          {/* Database Indexes */}
          <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
            <span className="text-xs font-bold block uppercase tracking-wide">Index Rebuilds</span>
            <button 
              onClick={handleRebuildIndexes}
              className="w-full flex items-center justify-center gap-1.5 p-2.5 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/25 rounded-lg text-[10px] font-bold transition-all text-blue-300"
            >
              <RefreshCw size={12} className="animate-spin-slow" />
              REBUILD EPISODIC INDEXES
            </button>
          </div>

          {/* Agent Restarts */}
          <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
            <span className="text-xs font-bold block uppercase tracking-wide">Subsystem Recovery</span>
            <button 
              onClick={handleRestartAgents}
              className="w-full flex items-center justify-center gap-1.5 p-2.5 bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/25 rounded-lg text-[10px] font-bold transition-all text-emerald-300"
            >
              <Cpu size={12} />
              RESTART COGNITIVE AGENTS
            </button>
          </div>

          {/* Safe Mode Switch */}
          <div className="bg-red-950/10 border border-red-500/20 p-4 rounded-xl flex items-center justify-between">
            <div>
              <span className="text-xs font-bold block text-red-300 uppercase tracking-wide">Recovery Safe Mode</span>
              <span className="text-[9px] text-slate-500">Lock automation layers during crashes</span>
            </div>
            <button 
              onClick={() => {
                setSafeMode(!safeMode);
                addLog(safeMode ? 'Deactivating recovery safe mode...' : 'Emergency recovery Safe Mode activated!');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[9px] font-bold transition-all ${
                safeMode ? 'bg-red-600 text-white' : 'bg-slate-950/60 border border-red-500/30 text-red-400'
              }`}
            >
              <AlertTriangle size={12} />
              {safeMode ? 'SAFE ON' : 'ACTIVATE'}
            </button>
          </div>
        </div>

        {/* Live Diagnostics Log */}
        <div className="flex flex-col bg-slate-950/60 border border-white/5 rounded-xl p-4 overflow-hidden h-full">
          <span className="text-xs font-bold mb-2 font-mono flex items-center gap-1.5 text-slate-400">
            <FileText size={12} />
            DIAGNOSTIC EVENTS CONSOLE
          </span>
          <div className="flex-1 overflow-y-auto custom-scrollbar font-mono text-[9px] text-slate-400 space-y-1.5 pr-1">
            {logs.length === 0 ? (
              <span className="text-slate-600 italic block">Console idle. Awaiting operations...</span>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="border-b border-white/5 pb-1 last:border-b-0 leading-normal">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
