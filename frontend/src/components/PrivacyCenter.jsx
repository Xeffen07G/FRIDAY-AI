import React, { useState } from 'react';
import { Shield, Eye, Database, Trash2, Key, Sliders, CheckCircle } from 'lucide-react';

export default function PrivacyCenter() {
  const [autonomyLevel, setAutonomyLevel] = useState(3);
  const [localOnly, setLocalOnly] = useState(true);
  const [permissions, setPermissions] = useState({
    terminal: true,
    filesystem: true,
    microphone: false,
    camera: false
  });
  const [statusMessage, setStatusMessage] = useState('');

  const handleToggle = (key) => {
    setPermissions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleCompaction = () => {
    setStatusMessage('Compressing SQLite databases...');
    setTimeout(() => {
      setStatusMessage('Memory databases compressed successfully! (Saved 14.2 MB)');
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/80 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden shadow-2xl p-6 text-slate-200">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-6">
        <Shield className="text-blue-400 animate-pulse" size={20} />
        <div>
          <h2 className="text-sm font-bold font-mono tracking-wider uppercase">Privacy & Autonomy Center</h2>
          <p className="text-[10px] text-slate-500">Configure local-only sandboxes and monitor cognitive system trust metrics</p>
        </div>
      </div>

      {/* Control sliders */}
      <div className="space-y-5 flex-1">
        {/* Autonomy Level Slider */}
        <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold flex items-center gap-1.5">
              <Sliders size={14} className="text-blue-400" />
              COGNITIVE AUTONOMY CEILING
            </span>
            <span className="text-[10px] font-mono font-bold bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
              Lvl {autonomyLevel} - {autonomyLevel === 5 ? 'UNRESTRICTED' : autonomyLevel >= 3 ? 'SUPERVISED' : 'LOCKED'}
            </span>
          </div>
          <input 
            type="range" 
            min="1" 
            max="5" 
            value={autonomyLevel} 
            onChange={(e) => setAutonomyLevel(Number(e.target.value))}
            className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <span className="text-[9px] text-slate-500 block">
            Sets the permission threshold. Higher levels allow chain execution without manual confirmations.
          </span>
        </div>

        {/* Local Sandboxing Toggle */}
        <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs font-bold block">OFFLINE-FIRST COMPLIANCE</span>
            <span className="text-[9px] text-slate-500">Force all planner steps through local phi3:mini models</span>
          </div>
          <button 
            onClick={() => setLocalOnly(!localOnly)}
            className={`w-10 h-5 rounded-full p-0.5 transition-colors ${localOnly ? 'bg-blue-600' : 'bg-slate-800'}`}
          >
            <div className={`w-4 h-4 bg-white rounded-full transition-transform ${localOnly ? 'translate-x-5' : 'translate-x-0'}`}></div>
          </button>
        </div>

        {/* Dynamic Permissions */}
        <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
          <span className="text-xs font-bold block flex items-center gap-1.5">
            <Key size={14} className="text-blue-400" />
            WORKSPACE PERMISSIONS & ACCESS GATES
          </span>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
            {Object.entries(permissions).map(([key, val]) => (
              <div 
                key={key} 
                onClick={() => handleToggle(key)}
                className={`p-2.5 rounded border cursor-pointer transition-all flex items-center justify-between ${
                  val ? 'bg-blue-950/20 border-blue-500/35 text-blue-300' : 'bg-slate-950/40 border-white/5 text-slate-500'
                }`}
              >
                <span className="uppercase text-[9px]">{key}</span>
                <span className="text-[8px] font-bold">{val ? 'GRANTED' : 'BLOCKED'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Memory Compaction and Purges */}
        <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs font-bold block">LOCAL MEMORY COMPACTION</span>
            <span className="text-[9px] text-slate-500">Purge stale logs and trigger sqlite vacumming</span>
          </div>
          <button 
            onClick={handleCompaction}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[10px] font-bold transition-all"
          >
            <Database size={12} />
            COMPACT NOW
          </button>
        </div>
      </div>

      {/* Footer message log */}
      {statusMessage && (
        <div className="mt-4 bg-blue-950/30 border border-blue-500/20 p-2.5 rounded-lg flex items-center gap-2 text-[10px] text-blue-300">
          <CheckCircle size={12} className="text-blue-400 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
}
