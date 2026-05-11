import { useState, useEffect } from 'react';

export default function DiagnosticsPanel({ isOpen, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/health');
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Health check failed", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHealth();
      const interval = setInterval(fetchHealth, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <h2 className="text-lg font-semibold text-slate-100">Production Diagnostics</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
          {data ? (
            <>
              {/* System Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">System RAM</p>
                  <p className="text-xl font-bold text-slate-200">{data.system.ram_percent}%</p>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">FRIDAY RAM</p>
                  <p className="text-xl font-bold text-slate-200">{data.system.friday_ram_mb} MB</p>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Active Tasks</p>
                  <p className="text-xl font-bold text-blue-400">{data.tasks.active_count}</p>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Models</p>
                  <p className="text-xl font-bold text-emerald-400">{data.models.active_models.length}</p>
                </div>
              </div>

              {/* Active Tasks */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Active Async Tasks</h3>
                <div className="space-y-2">
                  {data.tasks.tasks.length > 0 ? (
                    data.tasks.tasks.map(task => (
                      <div key={task.id} className="flex items-center justify-between p-3 bg-slate-950/50 rounded-lg border border-slate-800/50 font-mono text-[11px]">
                        <div className="flex items-center gap-3">
                          <span className={task.status === 'running' ? 'text-blue-400' : 'text-slate-500'}>
                            {task.status === 'running' ? '●' : '○'}
                          </span>
                          <span className="text-slate-300">{task.name}</span>
                        </div>
                        <span className="text-slate-500">{task.age.toFixed(1)}s</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-600 italic text-center py-4">No active background tasks</p>
                  )}
                </div>
              </div>

              {/* Loaded Models */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Ollama Runtime</h3>
                <div className="space-y-2">
                  {data.models.active_models.length > 0 ? (
                    data.models.active_models.map(model => (
                      <div key={model} className="flex items-center justify-between p-3 bg-slate-950/50 rounded-lg border border-slate-800/50 font-mono text-[11px]">
                        <span className="text-emerald-400 font-bold">{model}</span>
                        <span className="text-slate-500">LAST USED: {data.models.last_used[model] || 'N/A'}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-600 italic text-center py-4">No models currently loaded in VRAM</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-slate-500 font-mono text-xs">COLLECTING TELEMETRY...</p>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center text-[10px] font-mono text-slate-500 uppercase">
          <span>Version: {data?.version || '...'}</span>
          <button onClick={fetchHealth} className="hover:text-blue-400 transition-colors">Force Refresh</button>
        </div>
      </div>
    </div>
  );
}
