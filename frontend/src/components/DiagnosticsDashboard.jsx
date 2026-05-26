import React, { useMemo } from 'react';

const DiagnosticsDashboard = ({ metrics, isConnected, convState, onClose }) => {
  const stats = useMemo(() => {
    if (!metrics) return null;
    return {
      stt: metrics.stt_ms || 0,
      llm_first: metrics.first_token_ms || 0,
      llm_gen: metrics.generation_ms || 0,
      tts: metrics.tts_ms || 0,
      total: metrics.total_ms || 0,
      tokens_sec: metrics.generation_ms > 0 ? ((metrics.token_count || 0) / (metrics.generation_ms / 1000)).toFixed(1) : 0,
      intent: metrics.intent || 'N/A'
    };
  }, [metrics]);

  return (
    <div className="w-80 bg-slate-950 border border-slate-800 rounded-lg shadow-xl overflow-hidden font-mono flex flex-col">
      <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">System Telemetry</h3>
        <button onClick={onClose} className="p-1 text-slate-500 hover:text-slate-300 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
           <div className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-wider ${isConnected ? 'bg-slate-900 text-emerald-400 border border-slate-800' : 'bg-slate-900 text-rose-400 border border-slate-800'}`}>
             {isConnected ? 'LIVE_WS' : 'OFFLINE'}
           </div>
           <div className="text-[9px] text-slate-500">STATE: <span className="text-slate-300">{convState.toUpperCase()}</span></div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'STT', value: `${stats?.stt || 0}ms`, color: 'text-slate-300' },
            { label: 'FIRST', value: `${stats?.llm_first || 0}ms`, color: 'text-slate-300' },
            { label: 'TTS', value: `${stats?.tts || 0}ms`, color: 'text-slate-300' },
            { label: 'TPUT', value: `${stats?.tokens_sec || 0} t/s`, color: 'text-slate-300' }
          ].map((item, idx) => (
            <div key={idx} className="p-2.5 bg-slate-900/60 rounded border border-slate-800">
              <p className="text-[8px] text-slate-500 font-bold uppercase tracking-wider mb-0.5">{item.label}</p>
              <p className={`text-xs font-mono font-semibold ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>

        <div className="p-2.5 bg-slate-900 rounded border border-slate-800">
           <div className="flex items-center justify-between mb-0.5">
             <p className="text-[8px] text-slate-500 font-bold uppercase tracking-wider">Total Latency</p>
           </div>
           <p className="text-lg font-mono font-bold text-slate-250">{stats?.total || 0}ms</p>
        </div>

        <div className="space-y-1.5">
           <div className="flex justify-between text-[9px] text-slate-500">
             <span>INTENT</span>
             <span className="text-slate-300">{stats?.intent.toUpperCase()}</span>
           </div>
           <div className="h-1 bg-slate-900 rounded overflow-hidden">
             <div className="h-full bg-slate-700 w-3/4"></div>
           </div>
        </div>
      </div>

      <div className="px-4 py-2.5 bg-slate-900/60 text-[8px] text-slate-500 flex justify-between border-t border-slate-800">
         <span>CPU_LOAD: ~22%</span>
         <span>MEM: 4.2GB</span>
      </div>
    </div>
  );
};

export default DiagnosticsDashboard;
