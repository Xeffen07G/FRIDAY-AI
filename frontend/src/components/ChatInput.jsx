import { useState } from 'react';

export default function ChatInput({ onSend, isLoading }) {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
      onSend(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-slate-900/80 backdrop-blur-md border-t border-slate-800/80">
      <div className="max-w-4xl mx-auto relative flex items-center shadow-lg rounded-full overflow-hidden bg-slate-950 border border-slate-700 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all">
        <input
          type="text"
          className="w-full bg-transparent py-4 pl-6 pr-16 focus:outline-none text-slate-100 placeholder-slate-500"
          placeholder="Command F.R.I.D.A.Y..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          autoFocus
        />
        
        <button 
          onClick={handleSend}
          disabled={isLoading || !inputValue.trim()}
          className={`absolute right-2 p-2.5 rounded-full transition-all duration-200 ${
            inputValue.trim() && !isLoading 
              ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30' 
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  );
}
