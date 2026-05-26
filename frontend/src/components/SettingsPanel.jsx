import React, { useState } from 'react';
import { Zap } from 'lucide-react';
import { API_CONFIG } from '../config/api';

export default function SettingsPanel({ isOpen, onClose, quietMode, setQuietMode }) {
  const [demoEnabled, setDemoEnabled] = useState(false);
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-[#090a0c]/70 backdrop-blur-xl z-50 flex items-center justify-center p-4 animate-in fade-in duration-300">
      <div className="bg-obsidian-900 border border-white/[0.035] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-[0.985] duration-[280ms] ease-[cubic-bezier(0.16,1,0.3,1)]">
        <div className="p-6 border-b border-white/[0.025] flex items-center justify-between">
          <h2 className="text-lg font-bold font-sans text-slate-100 flex items-center gap-2.5">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1V15a2 2 0 0 1-2-2 2 2 0 0 1 2-2v-.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2v.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            System Configuration
          </h2>
          <button onClick={onClose} className="p-2 text-slate-500 hover:text-slate-200 hover:bg-obsidian-950 rounded-lg transition-premium press-tactile">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh] custom-scrollbar">
          {/* Atmosphere Settings */}
          <section className="space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-sans">Workspace Atmosphere</h3>
            <div className="space-y-4 bg-obsidian-950/20 p-4 border border-white/[0.015] rounded-xl">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-xs font-semibold text-slate-300">Quiet Mode</label>
                  <p className="text-[10px] text-slate-500 leading-normal">Mutes proactive prompts and telemetries for deep work focus.</p>
                </div>
                <button 
                  onClick={() => setQuietMode(!quietMode)}
                  className={`w-10 h-5 rounded-full relative transition-all duration-300 ${quietMode ? 'bg-blue-500/80' : 'bg-white/[0.08]'}`}
                >
                  <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${quietMode ? 'right-1' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </section>

          {/* Inference Settings */}
          <section className="space-y-4">
            <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest">Inference Engine</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Default Model</label>
                <select className="bg-obsidian-950 border border-white/[0.035] text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-white/[0.08] transition-premium font-sans font-semibold">
                  <option>phi3:mini</option>
                  <option>llama3:8b</option>
                  <option>mistral</option>
                </select>
              </div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Temperature</label>
                <input type="range" min="0" max="100" defaultValue="70" className="w-32 accent-slate-200" />
              </div>
            </div>
          </section>

          {/* Memory Settings */}
          <section className="space-y-4 pt-4 border-t border-white/[0.015]">
            <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Memory & RAG</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Retrieval Threshold</label>
                <input type="number" defaultValue="0.55" step="0.05" className="bg-obsidian-950 border border-white/[0.035] text-slate-200 text-xs rounded-lg px-3 py-2 w-20 outline-none focus:border-white/[0.08] transition-premium font-sans font-semibold" />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Auto-Extraction</label>
                <div className="w-10 h-5 bg-white/[0.08] hover:bg-white/[0.12] rounded-full relative cursor-pointer transition-premium press-tactile">
                  <div className="absolute right-1 top-1 w-3 h-3 bg-slate-300 rounded-full"></div>
                </div>
              </div>
            </div>
          </section>

          {/* Voice Settings */}
          <section className="space-y-4 pt-4 border-t border-white/[0.015]">
            <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest">Voice Pipeline</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Wake Word Detection</label>
                <div className="w-10 h-5 bg-obsidian-950 rounded-full relative cursor-pointer border border-white/[0.025] transition-premium press-tactile">
                  <div className="absolute left-1 top-0.5 w-3 h-3 bg-slate-600 rounded-full"></div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-350">Text-to-Speech</label>
                <select className="bg-obsidian-950 border border-white/[0.035] text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-white/[0.08] transition-premium font-sans font-semibold">
                  <option>Disabled</option>
                  <option>Piper (Local)</option>
                  <option>Web Speech API</option>
                </select>
              </div>
            </div>
          </section>

          {/* Showcase & Demo */}
          <section className="pt-4 border-t border-white/[0.025]">
            <h3 className="text-xs font-bold text-amber-500 uppercase tracking-widest flex items-center gap-2">
              <Zap size={12} /> Showcase & Demo
            </h3>
            <div className="bg-obsidian-950 border border-white/[0.025] p-4.5 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-xs font-semibold text-slate-300">Simulated Mode</label>
                  <p className="text-[10px] text-slate-500">Use pre-recorded snapshots for reliable demos.</p>
                </div>
                <button 
                  onClick={async () => {
                    const next = !demoEnabled;
                    setDemoEnabled(next);
                    try {
                      await fetch(`${API_CONFIG.ENDPOINTS.CHAT.replace('/chat', '')}/settings/demo?enabled=${next}`, { method: 'POST' });
                    } catch (e) { console.error(e); }
                  }}
                  className={`w-10 h-5 rounded-full relative transition-premium press-tactile ${demoEnabled ? 'bg-amber-600' : 'bg-white/[0.08]'}`}
                >
                  <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${demoEnabled ? 'right-1' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </section>
        </div>

        <div className="p-6 bg-[#090a0c]/80 border-t border-white/[0.025] flex justify-end items-center gap-4">
          <button onClick={onClose} className="px-4 py-2.5 text-xs font-semibold text-slate-450 hover:text-slate-205 transition-premium press-tactile">Cancel</button>
          <button 
            onClick={onClose}
            className="px-5 py-2.5 bg-white text-obsidian-950 hover:bg-slate-100 rounded-xl text-xs font-semibold transition-premium shadow-md press-tactile"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
