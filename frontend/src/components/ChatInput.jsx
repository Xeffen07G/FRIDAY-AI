import { useState, useRef, useEffect } from 'react';

export default function ChatInput({ 
  onSend, 
  onStop, 
  isLoading, 
  isRecording, 
  startRecording, 
  stopRecording, 
  convState,
  micEnergy = 0,
  partialTranscript = ''
}) {
  const [inputValue, setInputValue] = useState('');
  const fileInputRef = useRef(null);

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
      onSend(inputValue.trim());
      setInputValue('');
    }
  };

  const handleStop = () => {
    if (onStop) onStop();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log("Selected file:", file.name);
    }
  };

  // Determine button style based on conversational state
  const getMicButtonStyle = () => {
    switch (convState) {
      case 'listening':
        return 'bg-red-500/20 border-red-500 text-red-400 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.3)]';
      case 'transcribing':
        return 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse';
      case 'thinking':
        return 'bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse';
      case 'speaking':
        return 'bg-emerald-500/20 border-emerald-500 text-emerald-400 animate-pulse';
      default:
        return 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600';
    }
  };

  const scaleValue = convState === 'listening' ? 1 + (micEnergy / 255) * 0.3 : 1;

  return (
    <div className="p-4 bg-slate-900/80 backdrop-blur-md border-t border-slate-800/80 relative z-20">
      <div className="max-w-4xl mx-auto flex items-center gap-2 md:gap-3">
        {/* Voice Button */}
        <button 
          onClick={toggleMic}
          className={`p-3 rounded-full border transition-all duration-75 shrink-0 ${getMicButtonStyle()}`}
          title={isRecording ? "Stop Listening" : "Voice Command"}
          style={{ transform: `scale(${scaleValue})` }}
        >
          {convState === 'transcribing' ? (
             <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
          )}
        </button>

        {/* Attachment Button */}
        <button 
          onClick={handleFileClick}
          className="p-3 bg-slate-800/50 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 rounded-full transition-all shrink-0"
          title="Upload Image"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
        </button>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          className="hidden" 
          accept="image/*"
        />

        {/* Input Field */}
        <div className="flex-1 relative flex items-center shadow-lg rounded-full overflow-hidden bg-slate-950 border border-slate-700 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all">
          <input
            type="text"
            className="w-full bg-transparent py-3.5 pl-6 pr-16 focus:outline-none text-slate-100 placeholder-slate-500"
            placeholder={isRecording ? (partialTranscript || "Listening...") : "Command F.R.I.D.A.Y..."}
            value={isRecording ? partialTranscript : inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            readOnly={isRecording}
          />
          
          <div className="absolute right-1.5 flex items-center gap-1">
            {isLoading ? (
              <button 
                onClick={handleStop}
                className="p-2.5 bg-slate-800 hover:bg-slate-700 text-red-400 rounded-full transition-all duration-200 border border-slate-700/50 group"
                title="Stop Generation"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="group-hover:scale-110 transition-transform">
                  <rect x="6" y="6" width="12" height="12"></rect>
                </svg>
              </button>
            ) : (
              <button 
                onClick={handleSend}
                disabled={!inputValue.trim()}
                className={`p-2.5 rounded-full transition-all duration-200 ${
                  inputValue.trim()
                    ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                    : 'bg-slate-800/50 text-slate-600 cursor-not-allowed'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
