import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Mic, 
  Cpu, 
  Database, 
  Shield, 
  Zap, 
  MessageSquare, 
  Activity, 
  Layers,
  ArrowRight,
  Terminal,
  Server,
  Lock
} from 'lucide-react';

// Custom GitHub icon as lucide-react doesn't provide it in this version
const GithubIcon = ({ size = 24, ...props }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    {...props}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.5, delay }}
    className="glass-morphism p-6 rounded-2xl border border-white/5 hover:border-blue-500/30 transition-all group"
  >
    <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
      <Icon className="text-blue-400" size={24} />
    </div>
    <h3 className="text-lg font-bold mb-2 font-heading tracking-tight">{title}</h3>
    <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
  </motion.div>
);

const StatItem = ({ label, value }) => (
  <div className="flex flex-col items-center justify-center p-4">
    <span className="text-3xl font-bold text-white mb-1 font-heading">{value}</span>
    <span className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">{label}</span>
  </div>
);

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden selection:bg-blue-500/30">
      
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 backdrop-blur-md border-b border-white/5 bg-slate-950/20">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg neon-glow-blue">F</div>
             <span className="text-xl font-bold font-heading tracking-tighter">F.R.I.D.A.Y.</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <a href="#tech" className="hover:text-white transition-colors">Stack</a>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://github.com" target="_blank" className="p-2 text-slate-400 hover:text-white transition-colors">
              <GithubIcon size={20} />
            </a>
            <Link 
              to="/assistant" 
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-sm font-semibold transition-all shadow-lg shadow-blue-900/20 hover:scale-105 active:scale-95"
            >
              Launch System
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold tracking-[0.2em] uppercase mb-6">
              <Zap size={12} fill="currentColor" /> v2.0 - Cognitive OS
            </div>
            <h1 className="text-6xl lg:text-7xl font-bold font-heading leading-[1.1] mb-6 tracking-tighter">
              The Future of <span className="text-gradient">Local Presence.</span>
            </h1>
            <p className="text-lg text-slate-400 mb-10 leading-relaxed max-w-xl">
              F.R.I.D.A.Y. is a persistent, realtime AI operating system that lives on your hardware. 
              Zero-latency voice interaction, autonomous reasoning, and secure local memory.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link 
                to="/assistant" 
                className="group px-8 py-4 bg-white text-slate-950 rounded-2xl font-bold flex items-center gap-2 hover:bg-blue-50 transition-all shadow-xl hover:scale-105"
              >
                Launch Console <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <a 
                href="#architecture" 
                className="px-8 py-4 glass-morphism rounded-2xl font-bold text-white hover:bg-white/5 transition-all"
              >
                Explore Architecture
              </a>
            </div>
            
            <div className="mt-16 grid grid-cols-3 gap-8 border-t border-white/5 pt-8">
               <StatItem label="Latency" value="<200ms" />
               <StatItem label="Models" value="4 Active" />
               <StatItem label="Privacy" value="Offline" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9, rotate: 2 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="relative group"
          >
            <div className="absolute inset-0 bg-blue-600/20 rounded-[40px] blur-[60px] group-hover:bg-blue-500/30 transition-all duration-700"></div>
            <div className="relative glass-morphism rounded-[32px] p-2 border border-white/10 overflow-hidden shadow-2xl">
               <img 
                 src="https://images.unsplash.com/photo-1639322537228-f710d846310a?q=80&w=2000&auto=format&fit=crop" 
                 alt="F.R.I.D.A.Y. Interface" 
                 className="w-full h-auto rounded-[24px] grayscale-[20%] group-hover:grayscale-0 transition-all duration-700 hover:scale-[1.02]"
               />
               
               {/* Floating Overlay Stats */}
               <div className="absolute top-8 right-8 p-4 glass-morphism rounded-2xl border border-white/10 flex items-center gap-3 animate-bounce" style={{ animationDuration: '3s' }}>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></div>
                  <span className="text-[10px] font-mono font-bold text-slate-300">CORE_STABLE</span>
               </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold font-heading mb-4 tracking-tight">Built for Performance.</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Every component of F.R.I.D.A.Y. is optimized for high-speed local inference and secure data handling.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard 
              icon={Mic} 
              title="Realtime Voice" 
              description="Sub-second STT/TTS pipeline with Faster-Whisper and Piper synthesis."
              delay={0.1}
            />
            <FeatureCard 
              icon={Cpu} 
              title="Local Logic" 
              description="Runs entirely on your hardware using Ollama. No data ever leaves your machine."
              delay={0.2}
            />
            <FeatureCard 
              icon={Database} 
              title="Semantic Memory" 
              description="Persistent long-term memory powered by ChromaDB vector search."
              delay={0.3}
            />
            <FeatureCard 
              icon={Zap} 
              title="Autonomous Reasoning" 
              description="Goal-oriented planning engine with multi-step tool orchestration."
              delay={0.4}
            />
          </div>
        </div>
      </section>

      {/* Architecture Visualization */}
      <section id="architecture" className="py-24 px-6">
         <div className="max-w-5xl mx-auto">
            <div className="glass-morphism rounded-[40px] p-12 border border-white/5 relative overflow-hidden">
               <div className="absolute top-0 right-0 p-8">
                  <Activity className="text-blue-500/20" size={120} />
               </div>
               
               <div className="relative z-10">
                  <span className="text-blue-500 font-mono text-[10px] font-bold tracking-widest uppercase block mb-4">Internal Systems</span>
                  <h2 className="text-4xl font-bold font-heading mb-8 tracking-tight">Cognitive Architecture.</h2>
                  
                  <div className="space-y-8">
                     <div className="flex items-start gap-6 group">
                        <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center shrink-0 group-hover:border-blue-500/50 transition-colors">
                           <Layers className="text-slate-500 group-hover:text-blue-400 transition-colors" size={20} />
                        </div>
                        <div>
                           <h4 className="text-lg font-bold mb-1">Hierarchical Memory</h4>
                           <p className="text-sm text-slate-400">Working, Episodic, and Semantic memory layers with automatic decay and reinforcement.</p>
                        </div>
                     </div>

                     <div className="flex items-start gap-6 group">
                        <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center shrink-0 group-hover:border-blue-500/50 transition-colors">
                           <Shield className="text-slate-500 group-hover:text-blue-400 transition-colors" size={20} />
                        </div>
                        <div>
                           <h4 className="text-lg font-bold mb-1">Privacy Isolation</h4>
                           <p className="text-sm text-slate-400">Hardware-level isolation. All inference happens locally via GGUF/ExLlama runtimes.</p>
                        </div>
                     </div>

                     <div className="flex items-start gap-6 group">
                        <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center shrink-0 group-hover:border-blue-500/50 transition-colors">
                           <Terminal className="text-slate-500 group-hover:text-blue-400 transition-colors" size={20} />
                        </div>
                        <div>
                           <h4 className="text-lg font-bold mb-1">Tool Orchestrator</h4>
                           <p className="text-sm text-slate-400">A deterministic execution engine that routes user intent to system tools or background agents.</p>
                        </div>
                     </div>
                  </div>
                  
                  <div className="mt-12 flex gap-4">
                     <div className="px-4 py-2 bg-slate-900/50 rounded-lg border border-white/5 font-mono text-[10px] text-slate-500">
                        LATENCY_GEN: ~14ms/tk
                     </div>
                     <div className="px-4 py-2 bg-slate-900/50 rounded-lg border border-white/5 font-mono text-[10px] text-slate-500">
                        STT_STREAMS: ACTIVE
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </section>

      {/* Tech Stack */}
      <section id="tech" className="py-24 px-6 border-t border-white/5">
         <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-12 opacity-60 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-700">
               <div className="flex flex-col items-center gap-3">
                  <Server className="text-blue-400" size={40} />
                  <span className="font-bold text-sm">Ollama Core</span>
               </div>
               <div className="flex flex-col items-center gap-3">
                  <Zap className="text-amber-400" size={40} />
                  <span className="font-bold text-sm">FastAPI / Uvicorn</span>
               </div>
               <div className="flex flex-col items-center gap-3">
                  <Activity className="text-emerald-400" size={40} />
                  <span className="font-bold text-sm">Chroma Vector DB</span>
               </div>
               <div className="flex flex-col items-center gap-3">
                  <MessageSquare className="text-purple-400" size={40} />
                  <span className="font-bold text-sm">React / Vite / Tailwind</span>
               </div>
            </div>
         </div>
      </section>

      {/* CTA Footer */}
      <section className="py-24 px-6 bg-gradient-to-t from-blue-600/10 to-transparent">
         <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-5xl font-bold font-heading mb-8 tracking-tighter">Ready to evolve?</h2>
            <p className="text-slate-400 mb-10 text-lg">
               Join the private local AI revolution. Deploy F.R.I.D.A.Y. on your workstation today.
            </p>
            <div className="flex justify-center gap-6">
                <Link to="/assistant" className="px-10 py-5 bg-white text-slate-950 rounded-2xl font-bold hover:scale-105 transition-all shadow-2xl">
                   Get Started Locally
                </Link>
                <a href="https://github.com" className="px-10 py-5 glass-morphism rounded-2xl font-bold hover:bg-white/5 transition-all flex items-center gap-2">
                   <GithubIcon size={20} /> View Source
                </a>
            </div>
         </div>
      </section>

      <footer className="py-12 px-6 border-t border-white/5 text-center text-slate-600 text-xs font-mono tracking-widest uppercase">
         © 2026 Advanced Agentic Coding // PROJECT_FRIDAY_OS
      </footer>
    </div>
  );
}
