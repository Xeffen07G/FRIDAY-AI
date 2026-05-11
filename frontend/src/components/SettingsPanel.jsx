import React from 'react';

export default function SettingsPanel({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1V15a2 2 0 0 1-2-2 2 2 0 0 1 2-2v-.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2v.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            System Configuration
          </h2>
          <button onClick={onClose} className="p-2 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh] custom-scrollbar">
          {/* Inference Settings */}
          <section>
            <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-widest mb-4">Inference Engine</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Default Model</label>
                <select className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg p-2 outline-none focus:border-blue-500">
                  <option>phi3:mini</option>
                  <option>llama3:8b</option>
                  <option>mistral</option>
                </select>
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Temperature</label>
                <input type="range" min="0" max="100" defaultValue="70" className="w-32 accent-blue-500" />
              </div>
            </div>
          </section>

          {/* Memory Settings */}
          <section>
            <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-widest mb-4">Memory & RAG</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Retrieval Threshold</label>
                <input type="number" defaultValue="0.55" step="0.05" className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg p-2 w-20 outline-none focus:border-blue-500" />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Auto-Extraction</label>
                <div className="w-10 h-5 bg-blue-600 rounded-full relative cursor-pointer">
                  <div className="absolute right-1 top-1 w-3 h-3 bg-white rounded-full"></div>
                </div>
              </div>
            </div>
          </section>

          {/* Voice Settings */}
          <section>
            <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-widest mb-4">Voice Pipeline</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Wake Word Detection</label>
                <div className="w-10 h-5 bg-slate-800 rounded-full relative cursor-pointer">
                  <div className="absolute left-1 top-1 w-3 h-3 bg-slate-400 rounded-full"></div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-300">Text-to-Speech</label>
                <select className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg p-2 outline-none focus:border-blue-500">
                  <option>Disabled</option>
                  <option>Piper (Local)</option>
                  <option>Web Speech API</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        <div className="p-6 bg-slate-950/50 border-t border-slate-800 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200">Cancel</button>
          <button className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-900/20">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
