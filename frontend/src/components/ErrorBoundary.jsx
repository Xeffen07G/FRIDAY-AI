import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("F.R.I.D.A.Y. Frontend Crash:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-[#0a0a0a] text-white p-8 text-center">
          <h1 className="text-4xl font-bold text-red-500 mb-4 italic">Core System Failure</h1>
          <p className="text-gray-400 mb-6 max-w-md">
            F.R.I.D.A.Y. frontend encountered a critical runtime error. This might be due to a malformed response or a state synchronization issue.
          </p>
          <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-lg mb-8 text-left font-mono text-sm overflow-auto max-w-2xl">
            {this.state.error && this.state.error.toString()}
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-full font-medium transition-all"
          >
            Reboot Interface
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
