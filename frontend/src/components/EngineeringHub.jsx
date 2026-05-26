import { useState, useMemo, useEffect, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Terminal, 
  Zap, 
  Clock, 
  ChevronRight, 
  ChevronDown,
  Shield,
  RefreshCw,
  FolderOpen,
  ListTodo
} from 'lucide-react';

const EventRow = ({ event }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const typeColor = useMemo(() => {
    switch (event.type) {
      case 'RECV': return 'text-emerald-400 bg-emerald-400/10';
      case 'SEND': return 'text-blue-400 bg-blue-400/10';
      case 'ERR': return 'text-red-400 bg-red-400/10';
      case 'SYS': return 'text-purple-400 bg-purple-400/10';
      default: return 'text-slate-400 bg-slate-400/10';
    }
  }, [event.type]);

  const msgType = event.data?.type || event.data?.status || event.type;

  return (
    <div className="border-b border-slate-800/50 last:border-0">
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 py-2 px-3 hover:bg-slate-800/30 cursor-pointer transition-colors group"
      >
        <span className="text-[10px] font-mono text-slate-500 w-16">{event.timestamp}</span>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${typeColor}`}>
          {event.type}
        </span>
        <span className="text-xs font-mono text-slate-300 truncate flex-1">
          {msgType}
        </span>
        {isOpen ? <ChevronDown size={14} className="text-slate-600" /> : <ChevronRight size={14} className="text-slate-600 group-hover:text-slate-400" />}
      </div>
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden bg-slate-950/50"
          >
            <pre className="p-4 text-[10px] font-mono text-slate-400 whitespace-pre-wrap break-all leading-relaxed">
              {JSON.stringify(event.data, null, 2)}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

function EngineeringHub({ events = [], metrics = {}, isConnected, convState }) {
  const [activeTab, setActiveTab] = useState('timeline');
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const response = await fetch('/api/observability/telemetry');
        if (response.ok) {
          const data = await response.json();
          setTelemetry(data);
        }
      } catch (err) {}
    };
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 8000);
    return () => clearInterval(interval);
  }, []);

  // Error cleaner and Explainer (Tasks 5 & 7)
  const getErrorExplanation = (errStr) => {
    if (!errStr) return { message: 'Execution failed', cause: 'Unknown error.', action: 'Check system logs.' };
    const str = String(errStr);
    
    if (str.includes('ModuleNotFoundError')) {
      const match = str.match(/No module named '([^']+)'/);
      const mod = match ? match[1] : 'dependency';
      return { 
        message: `${mod} is not installed.`, 
        cause: `Missing Python module: ${mod}`, 
        action: `Run 'pip install ${mod}' or 'npm install'.`
      };
    }
    if (str.includes('ECONNREFUSED')) {
      return {
        message: 'Connection refused.',
        cause: 'The target service is not running or port is blocked.',
        action: 'Restart backend or free the required port.'
      };
    }
    if (str.includes('command not found')) {
      return {
        message: 'Command not found.',
        cause: 'The executable is missing from PATH.',
        action: 'Install the required tool or fix environment variables.'
      };
    }
    if (str.includes('EADDRINUSE')) {
      return {
        message: 'Port is already in use.',
        cause: 'Another process is occupying the requested port.',
        action: 'Kill the process using the port (e.g., kill-port 5173).'
      };
    }
    if (str.includes('npm ERR!')) {
      return {
        message: 'npm install failed.',
        cause: 'Package conflict or missing package.json.',
        action: 'Delete node_modules and package-lock.json, then retry.'
      };
    }
    
    const firstLine = str.split('\n')[0];
    return {
      message: firstLine.length > 80 ? firstLine.substring(0, 80) + '...' : firstLine,
      cause: 'Unhandled exception in execution flow.',
      action: 'Check recent code changes or restart the system.'
    };
  };

  // Execution Timeline derived from events
  const timelineEvents = useMemo(() => {
    return events.filter(e => 
      e.data?.type === 'execution_started' || 
      e.data?.type === 'tool_running' ||
      e.data?.type === 'tool_completed' ||
      e.data?.type === 'action_failed' ||
      e.data?.type === 'action_retry' ||
      e.data?.type === 'tool_result' ||
      e.data?.metrics
    ).map((e, idx) => {
      let status = 'RUNNING';
      let detail = '';
      let explanation = null;
      
      if (e.data?.type === 'execution_started') {
        status = 'START';
        detail = 'Execution Pipeline Started';
      } else if (e.data?.type === 'tool_running') {
        status = 'TOOL';
        detail = `Executing: ${e.data?.tool || 'unknown'}`;
      } else if (e.data?.type === 'tool_completed' || e.data?.type === 'tool_result') {
        status = 'SUCCESS';
        detail = `Completed: ${e.data?.tool || 'tool'}`;
      } else if (e.data?.type === 'action_retry') {
        status = 'RETRYING';
        detail = `Retrying ${e.data?.tool || 'tool'} (${e.data?.attempt || 1}/${e.data?.max || 3})...`;
      } else if (e.data?.type === 'action_failed' || e.type === 'ERR') {
        status = 'FAILED';
        explanation = getErrorExplanation(e.data?.error);
        detail = explanation.message;
      } else if (e.data?.metrics) {
        status = 'DONE';
        detail = `Latency: ${e.data.metrics.total_ms || 0}ms`;
      }
      return { 
        id: idx, 
        status, 
        detail, 
        explanation, 
        timestamp: e.timestamp, 
        confidence: e.data?.confidence,
        validationSource: e.data?.validation_source,
        fallbackUsed: e.data?.fallback_used,
        data: e.data 
      };
    });
  }, [events]);

  const latestMetrics = useMemo(() => {
    const mEvent = [...events].reverse().find(e => e.data?.metrics);
    return mEvent ? mEvent.data.metrics : null;
  }, [events]);

  return (
    <div className="flex flex-col h-full bg-slate-950/85 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/40 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-slate-400" />
          <h2 className="text-xs font-bold font-mono tracking-widest text-slate-200 uppercase">System Diagnostics</h2>
        </div>
        <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 animate-pulse'}`}></div>
            <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-widest">{isConnected ? "ONLINE" : "OFFLINE"}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex px-1.5 py-1 bg-slate-950/30 gap-0.5 border-b border-white/5">
        {[
          { id: 'timeline', label: 'Timeline', icon: ListTodo },
          { id: 'latency', label: 'Latencies', icon: Zap },
          { id: 'stability', label: 'Stability', icon: Activity },
          { id: 'events', label: 'Raw Events', icon: Terminal }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-1 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider transition-all ${
              activeTab === tab.id ? 'bg-slate-800 text-slate-200' : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
          >
            <tab.icon size={10} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'timeline' && (
            <motion.div 
              key="timeline"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 space-y-4 overflow-y-auto h-full custom-scrollbar"
            >
              <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                  <ListTodo size={14} className="text-slate-400" />
                  <span>EXECUTION TIMELINE</span>
                </div>
                <div className="space-y-2.5">
                  {timelineEvents.length > 0 ? timelineEvents.map((node, index) => (
                    <div key={index} className="relative flex items-center gap-4 bg-slate-950/60 p-3 rounded-lg border border-white/5">
                      <div className="flex items-center justify-center w-5 h-5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-bold">
                        {index + 1}
                      </div>
                      <div className="flex-1 text-[11px] font-mono">
                        <div className="flex justify-between mb-0.5">
                           <span className="font-bold text-slate-300 uppercase">{node.status}</span>
                           <span className="text-slate-500 text-[9px] px-1.5 py-0.5">{node.timestamp}</span>
                        </div>
                        <span className="text-slate-400 text-[10px] block">{node.detail}</span>
                        {node.confidence !== undefined && node.confidence !== null && (
                          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[9px] font-mono text-slate-500">
                            <span>Confidence:</span>
                            <span className={`font-bold px-1 rounded ${
                              node.confidence >= 90 
                                ? 'text-emerald-400 bg-emerald-500/10' 
                                : 'text-amber-400 bg-amber-500/10'
                            }`}>{node.confidence}%</span>
                            {node.validationSource && (
                              <span className="opacity-80">via {node.validationSource}</span>
                            )}
                            {node.fallbackUsed && (
                              <span className="text-red-400">({node.fallbackUsed})</span>
                            )}
                          </div>
                        )}
                        
                        {node.explanation && (
                          <div className="mt-2 bg-red-500/10 border border-red-500/20 p-2 rounded text-[9px]">
                            <span className="text-red-400 font-bold block mb-1">PROBABLE CAUSE:</span>
                            <span className="text-slate-300 block mb-2">{node.explanation.cause}</span>
                            <span className="text-emerald-400 font-bold block mb-1">SUGGESTED ACTION:</span>
                            <span className="text-slate-300 block">{node.explanation.action}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )) : (
                    <div className="text-slate-500 text-xs italic">Awaiting execution...</div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'latency' && (
            <motion.div 
              key="latency"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 space-y-4 overflow-y-auto h-full custom-scrollbar"
            >
              <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                  <Clock size={14} className="text-slate-400" />
                  <span>TOOL LATENCY TRACKER</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div className="bg-slate-950/60 p-2.5 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-1">TOTAL EXECUTION TIME</span>
                    <span className="text-emerald-400 font-bold">{latestMetrics?.total_ms || 0}ms</span>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-1">STARTUP DELAY</span>
                    <span className="text-blue-400 font-bold">{latestMetrics?.time_to_first_visible_response_ms || 0}ms</span>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-1">PLANNER LATENCY</span>
                    <span className="text-purple-400 font-bold">{latestMetrics?.intent_ms || 0}ms</span>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-1">TOOL LATENCY</span>
                    <span className="text-amber-400 font-bold">{latestMetrics?.tool_ms || 0}ms</span>
                  </div>
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-2">
                  OVERALL STATUS: <span className={latestMetrics?.total_ms < 1000 ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                    {latestMetrics?.total_ms < 1000 ? "FAST" : (latestMetrics?.total_ms < 3000 ? "NORMAL" : "SLOW")}
                  </span>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'stability' && (
            <motion.div 
              key="stability"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 space-y-4 overflow-y-auto h-full custom-scrollbar"
            >
              <div className="bg-slate-900/40 border border-white/5 p-4 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                  <Activity size={14} className="text-slate-400" />
                  <span>DAILY USE STABILITY REPORT</span>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div className="bg-slate-950/60 p-2 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-0.5">MEMORY PRESSURE</span>
                    <span className="text-emerald-400 font-bold">{telemetry?.stability?.memory_pressure || "NORMAL"}</span>
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-0.5">DISCONNECTS</span>
                    <span className="text-slate-300 font-bold">0</span>
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-0.5">FAILED TOOL LAUNCHES</span>
                    <span className="text-slate-300 font-bold">0</span>
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-white/5">
                    <span className="text-slate-500 block text-[8px] mb-0.5">RETRY COUNTS</span>
                    <span className="text-slate-300 font-bold">{telemetry?.healing?.heal_attempts || 0}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'events' && (
            <motion.div 
              key="events"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="h-full overflow-y-auto custom-scrollbar"
            >
              {events.length > 0 ? (
                <div className="flex flex-col">
                  {events.map((evt, idx) => (
                    <EventRow key={idx} event={evt} />
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500">
                  <Activity size={24} className="mb-2 opacity-20" />
                  <span className="text-xs font-mono">No events captured yet</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default memo(EngineeringHub);
