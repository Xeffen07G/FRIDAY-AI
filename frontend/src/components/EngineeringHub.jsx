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
  Monitor,
  HardDrive,
  Layout,
  FileText,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Briefcase,
  Globe
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
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEvents = useMemo(() => {
    if (!searchQuery) return events;
    return events.filter(e => 
      JSON.stringify(e.data).toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [events, searchQuery]);

  const healthStatus = useMemo(() => {
    return {
        ws: isConnected ? 'OPTIMAL' : 'OFFLINE',
        cpu: metrics?.cpu_percent < 80 ? 'STABLE' : 'STRESSED',
        memory: 'READY',
        index: 'SYNCED'
    };
  }, [isConnected, metrics]);

  return (
    <div className="flex flex-col h-full glass-morphism rounded-2xl border border-white/5 overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/40 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-blue-400" />
          <h2 className="text-sm font-bold font-heading tracking-tight">ENGINEERING HUB</h2>
        </div>
        <div className="flex items-center gap-2">
            <div className="hidden xl:flex items-center gap-3 mr-4 border-r border-white/5 pr-4">
                {Object.entries(healthStatus).map(([key, status]) => (
                    <div key={key} className="flex items-center gap-1.5">
                        <div className={`w-1 h-1 rounded-full ${status === 'OPTIMAL' || status === 'STABLE' || status === 'READY' || status === 'SYNCED' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                        <span className="text-[8px] font-mono text-slate-500 uppercase">{key}</span>
                    </div>
                ))}
            </div>
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 animate-pulse'}`}></div>
            <span className="text-[9px] font-mono font-bold text-slate-500 uppercase tracking-widest">{convState}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex px-2 py-1 bg-slate-950/30 gap-1">
        {[
          { id: 'events', label: 'Inspector', icon: Activity },
          { id: 'performance', label: 'Latency', icon: Zap },
          { id: 'memory', label: 'Memory', icon: Database },
          { id: 'desktop', label: 'Desktop', icon: Monitor },
          { id: 'workflow', label: 'Workflow', icon: Briefcase }
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
              <div className="p-3 border-b border-white/5 bg-slate-950/20">
                <div className="relative">
                  <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input 
                    type="text"
                    placeholder="Search logs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-900/50 border border-white/10 rounded-lg py-1.5 pl-8 pr-3 text-[10px] font-mono focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>
              </div>
              {filteredEvents.length > 0 ? (
                filteredEvents.map(event => <EventRow key={event.id} event={event} />)
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
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Execution Mode</span>
                    <span className={`text-sm font-bold font-heading uppercase ${metrics?.execution_mode === 'deterministic' ? 'text-emerald-400' : 'text-blue-400'}`}>
                        {metrics?.execution_mode || 'standby'}
                    </span>
                 </div>
                 <div className="glass-morphism p-4 rounded-xl border border-white/5">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">LLM Bypass</span>
                    <span className={`text-sm font-bold font-heading uppercase ${metrics?.llm_bypassed ? 'text-emerald-400' : 'text-slate-500'}`}>
                        {metrics?.llm_bypassed ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                 </div>
              </div>

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

          {activeTab === 'desktop' && (
            <motion.div 
              key="desktop"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-6 space-y-6 overflow-y-auto h-full custom-scrollbar"
            >
               <div className="grid grid-cols-2 gap-4">
                  <div className="glass-morphism p-4 rounded-xl border border-white/5">
                     <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Index Health</span>
                     <span className="text-sm font-bold text-emerald-400">OPTIMAL</span>
                  </div>
                  <div className="glass-morphism p-4 rounded-xl border border-white/5">
                     <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Runtime</span>
                     <span className="text-sm font-bold text-blue-400">BACKGROUND</span>
                  </div>
               </div>

               <div className="space-y-4">
                  <h5 className="text-[10px] font-mono text-slate-500 uppercase tracking-[0.2em] mb-3">Live Workspace Feed</h5>
                  {events.filter(e => e.data?.component === 'desktop').length > 0 ? (
                    events.filter(e => e.data?.component === 'desktop').slice(0, 8).map(e => (
                      <div key={e.id} className="flex items-center gap-3 p-3 bg-slate-900/30 rounded-lg border border-white/5">
                        <div className="p-1.5 rounded bg-blue-500/10 text-blue-400">
                          {e.data.type === 'file_indexed' ? <FileText size={12} /> : <Activity size={12} />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-bold text-slate-300 truncate">{e.data.data.name || e.data.data.action}</p>
                          <p className="text-[8px] font-mono text-slate-500 truncate">{e.data.data.path}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 border-2 border-dashed border-slate-800 rounded-2xl">
                       <p className="text-[10px] font-mono text-slate-600 uppercase tracking-widest">No Desktop Activity</p>
                    </div>
                  )}
               </div>

               <div className="p-4 bg-purple-500/5 border border-purple-500/20 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <Layout size={12} className="text-purple-400" />
                    <span className="text-[10px] font-mono text-purple-300 uppercase tracking-widest">Active Context</span>
                  </div>
                  <p className="text-[10px] text-slate-400 leading-relaxed italic">
                    Privacy Gate Active: Continuous surveillance disabled. Context is only analyzed on explicit request.
                  </p>
               </div>
            </motion.div>
          )}
          {activeTab === 'workflow' && (
            <motion.div 
              key="workflow"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-6 space-y-6 overflow-y-auto h-full custom-scrollbar"
            >
              <div className="space-y-6">
                <section>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
                        <Briefcase size={12} className="text-blue-500" />
                        Active Projects
                    </h3>
                    <div className="grid grid-cols-1 gap-2">
                        {metrics?.desktop?.projects?.length > 0 ? (
                            metrics.desktop.projects.map(p => (
                                <div key={p} className="p-3 rounded-xl bg-slate-900/50 border border-white/5 flex items-center justify-between">
                                    <span className="text-xs font-mono text-slate-300">{p}</span>
                                    <span className="text-[8px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">VS CODE</span>
                                </div>
                            ))
                        ) : (
                            <div className="text-xs text-slate-600 italic p-3 border border-dashed border-slate-800 rounded-xl text-center">No active projects detected</div>
                        )}
                    </div>
                </section>

                <section>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
                        <Globe size={12} className="text-emerald-500" />
                        Research Context
                    </h3>
                    <div className="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-3">
                        <div className="flex items-center justify-between border-b border-white/5 pb-2">
                            <span className="text-[10px] text-slate-400 uppercase font-mono">Status</span>
                            <span className="text-[10px] text-emerald-400 font-bold">READY</span>
                        </div>
                        <p className="text-[10px] text-slate-500 leading-relaxed italic">
                            Browser tab snapshots and article highlights are stored locally in the workflow memory core.
                        </p>
                    </div>
                </section>

                <section>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
                        <Clock size={12} className="text-purple-500" />
                        Recent Continuity
                    </h3>
                    <div className="space-y-2">
                        {events.filter(e => e.type === 'SYS' && e.data?.action?.startsWith('SAVE_')).slice(0, 3).map(e => (
                            <div key={e.id} className="p-2 rounded-lg bg-slate-900/20 border border-white/5 flex items-center justify-between text-[10px] font-mono">
                                <span className="text-slate-400">{e.data.action}</span>
                                <span className="text-slate-600">{e.timestamp}</span>
                            </div>
                        ))}
                    </div>
                </section>
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
