import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Terminal, 
  Database, 
  Zap, 
  Clock, 
  ChevronRight, 
  ChevronDown,
  AlertCircle,
  ArrowUpRight,
  ArrowDownLeft,
  Cpu,
  Monitor
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

const LatencyBar = ({ label, value, max = 2000, color = "bg-blue-500" }) => {
  const percentage = Math.min(100, (value / max) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] font-mono">
        <span className="text-slate-500 uppercase">{label}</span>
        <span className={value > 1500 ? 'text-red-400' : 'text-slate-300'}>{value}ms</span>
      </div>
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          className={`h-full ${color} rounded-full`}
        />
      </div>
    </div>
  );
};

export default function EngineeringHub({ events, metrics, isConnected, convState }) {
  const [activeTab, setActiveTab] = useState('events');

  return (
    <div className="flex flex-col h-full glass-morphism rounded-2xl border border-white/5 overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/40 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-blue-400" />
          <h2 className="text-sm font-bold font-heading tracking-tight">ENGINEERING HUB</h2>
        </div>
        <div className="flex items-center gap-2">
           <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 animate-pulse'}`}></div>
           <span className="text-[9px] font-mono font-bold text-slate-500 uppercase tracking-widest">{convState}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex px-2 py-1 bg-slate-950/30 gap-1">
        {[
          { id: 'events', label: 'Inspector', icon: Activity },
          { id: 'performance', label: 'Latency', icon: Zap },
          { id: 'memory', label: 'Memory', icon: Database }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
              activeTab === tab.id ? 'bg-blue-600/20 text-blue-400 shadow-inner' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <tab.icon size={12} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'events' && (
            <motion.div 
              key="events"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full overflow-y-auto custom-scrollbar"
            >
              {events.length > 0 ? (
                events.map(event => <EventRow key={event.id} event={event} />)
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3 opacity-50">
                  <Monitor size={32} />
                  <span className="text-[10px] font-mono uppercase tracking-[0.2em]">Awaiting Data Streams...</span>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'performance' && (
            <motion.div 
              key="perf"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-6 space-y-6"
            >
              <div className="grid grid-cols-2 gap-4">
                 <div className="glass-morphism p-4 rounded-xl border border-white/5">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">STT Offset</span>
                    <span className="text-xl font-bold text-white font-heading">{metrics?.stt_ms || 0}<span className="text-xs text-slate-500 ml-1">ms</span></span>
                 </div>
                 <div className="glass-morphism p-4 rounded-xl border border-white/5">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Inference</span>
                    <span className="text-xl font-bold text-white font-heading">{metrics?.generation_ms || 0}<span className="text-xs text-slate-500 ml-1">ms</span></span>
                 </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-white/5">
                 <LatencyBar label="Speech Recognition" value={metrics?.stt_ms || 0} color="bg-emerald-500" />
                 <LatencyBar label="Knowledge Retrieval" value={metrics?.retrieval_ms || 0} color="bg-purple-500" />
                 <LatencyBar label="Cognitive Reasoning" value={metrics?.generation_ms || 0} color="bg-blue-500" />
                 <LatencyBar label="Speech Synthesis" value={metrics?.tts_ms || 0} color="bg-amber-500" />
                 <div className="pt-2">
                    <LatencyBar label="End-to-End Latency" value={metrics?.total_ms || 0} max={4000} color="bg-gradient-to-r from-blue-500 to-purple-500" />
                 </div>
              </div>
              
              <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl flex items-start gap-3">
                 <AlertCircle size={14} className="text-blue-400 mt-0.5 shrink-0" />
                 <p className="text-[10px] text-blue-300/80 leading-relaxed">
                    Performance baseline established using local <b>phi3:mini</b>. Real-time targets set at sub-2.5s total loop duration.
                 </p>
              </div>
            </motion.div>
          )}

          {activeTab === 'memory' && (
            <motion.div 
              key="mem"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-6 space-y-6"
            >
               <div className="flex items-center gap-4 p-4 glass-morphism rounded-xl border border-white/5">
                  <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <Database size={20} className="text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold font-heading">Chroma Vector Core</h4>
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Active: persistence_layer_v1</span>
                  </div>
               </div>

               <div className="space-y-4">
                  <h5 className="text-[10px] font-mono text-slate-500 uppercase tracking-[0.2em] mb-3">Live Retrieval Logs</h5>
                  {events.filter(e => e.data?.type === 'metrics' && e.data?.data?.retrieval_ms).length > 0 ? (
                    events.filter(e => e.data?.type === 'metrics' && e.data?.data?.retrieval_ms).slice(0, 5).map(e => (
                      <div key={e.id} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-white/5">
                        <div className="flex items-center gap-3">
                          <Clock size={12} className="text-slate-500" />
                          <span className="text-[10px] font-mono text-slate-300">Semantic Query Resolved</span>
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400">-{e.data.data.retrieval_ms}ms</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 border-2 border-dashed border-slate-800 rounded-2xl">
                       <p className="text-[10px] font-mono text-slate-600 uppercase tracking-widest">No active retrievals</p>
                    </div>
                  )}
               </div>

               <div className="pt-6 border-t border-white/5 flex gap-4">
                  <div className="flex-1 text-center p-3 glass-morphism rounded-xl border border-white/5">
                    <span className="text-[9px] font-mono text-slate-500 uppercase block mb-1">Dimensions</span>
                    <span className="text-sm font-bold text-white">384</span>
                  </div>
                  <div className="flex-1 text-center p-3 glass-morphism rounded-xl border border-white/5">
                    <span className="text-[9px] font-mono text-slate-500 uppercase block mb-1">Index Type</span>
                    <span className="text-sm font-bold text-white uppercase">HNSW</span>
                  </div>
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Footer Info */}
      <div className="px-4 py-2 bg-slate-900/60 border-t border-white/5 flex items-center justify-between">
         <div className="flex items-center gap-4 text-[9px] font-mono text-slate-500">
            <span className="flex items-center gap-1"><Cpu size={10} /> BUS_CLK: 12.4GHz</span>
            <span className="flex items-center gap-1 uppercase tracking-widest text-blue-400/60">Node: v2.4.0_Stable</span>
         </div>
         <div className="flex items-center gap-1 text-[9px] font-mono text-slate-600">
            FRIDAY_ENGINE_RUNNING
         </div>
      </div>
    </div>
  );
}
