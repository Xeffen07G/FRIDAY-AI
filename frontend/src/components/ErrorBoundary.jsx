import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.setState({ errorInfo });
  }

  parseErrorDetails() {
    let file = 'Unknown';
    let component = 'Unknown';
    let stackSummary = '';

    const error = this.state.error;
    const errorInfo = this.state.errorInfo;

    if (error && error.stack) {
      stackSummary = error.stack.split('\n').slice(0, 8).join('\n');

      const stackLines = error.stack.split('\n');
      for (const line of stackLines) {
        const match = line.match(/at\s+([^\s(]+)\s+\(([^)]+)\)/) || line.match(/at\s+()([^)]+)/);
        if (match) {
          component = match[1] || component;
          const fullPath = match[2];
          if (fullPath) {
            const fileMatch = fullPath.match(/([^/\\?]+(?::\d+){0,2})(?:\?|$)/);
            if (fileMatch) {
              file = fileMatch[1];
              break;
            }
          }
        }
      }
    }

    if (errorInfo && errorInfo.componentStack) {
      const compLines = errorInfo.componentStack.split('\n').filter(line => line.trim());
      if (compLines.length > 0) {
        const firstLine = compLines[0].trim();
        const compMatch = firstLine.match(/in\s+([^\s(]+)/);
        if (compMatch) {
          component = compMatch[1];
        }
        const fileMatch = firstLine.match(/at\s+([^\s)]+)/);
        if (fileMatch) {
          const fullPath = fileMatch[1];
          const basenameMatch = fullPath.match(/([^/\\?]+)(?:\?|$)/);
          if (basenameMatch) {
            file = basenameMatch[1];
          }
        }
      }

      if (!stackSummary && errorInfo.componentStack) {
        stackSummary = errorInfo.componentStack.trim();
      }
    }

    return { file, component, stackSummary };
  }

  render() {
    if (this.state.hasError) {
      const { file, component, stackSummary } = this.parseErrorDetails();

      // Inline styles so this works even when CSS/Tailwind fails to load
      const containerStyle = {
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', background: '#090a0c', color: '#e2e8f0', padding: '24px',
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif", textAlign: 'center'
      };
      const headingStyle = { fontSize: '20px', fontWeight: 700, marginBottom: '8px', color: '#f1f5f9', letterSpacing: '-0.01em' };
      const errorMsgStyle = { fontSize: '14px', color: '#94a3b8', maxWidth: '560px', marginBottom: '24px', lineHeight: 1.6 };
      const btnStyle = {
        padding: '10px 20px', background: '#dc2626', color: '#fff', border: 'none', borderRadius: '12px',
        fontSize: '13px', fontWeight: 600, cursor: 'pointer', letterSpacing: '0.02em'
      };
      const detailBoxStyle = {
        marginTop: '32px', maxWidth: '640px', width: '100%', background: '#121316',
        border: '1px solid rgba(255,255,255,0.03)', borderRadius: '16px', padding: '24px',
        textAlign: 'left', fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#94a3b8'
      };
      const labelStyle = { color: '#64748b', marginRight: '8px', userSelect: 'none' };
      const fileValStyle = { color: '#f87171', fontWeight: 600 };
      const compValStyle = { color: '#60a5fa', fontWeight: 600 };
      const preStyle = {
        padding: '16px', background: '#050607', borderRadius: '12px', fontSize: '10.5px', color: '#64748b',
        overflow: 'auto', border: '1px solid rgba(255,255,255,0.015)', maxHeight: '200px',
        whiteSpace: 'pre-wrap', lineHeight: 1.6, marginTop: '8px'
      };
      const rowStyle = { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' };

      return (
        <div style={containerStyle}>
          <h1 style={headingStyle}>Something went wrong</h1>
          <p style={errorMsgStyle}>
            Error: {this.state.error?.message || this.state.error?.toString()}
          </p>
          <button style={btnStyle} onClick={() => window.location.reload()}>
            Reload
          </button>

          <div style={detailBoxStyle}>
            <div style={rowStyle}>
              <span style={labelStyle}>file:</span>
              <span style={fileValStyle}>{file}</span>
            </div>
            <div style={rowStyle}>
              <span style={labelStyle}>component:</span>
              <span style={compValStyle}>{component}</span>
            </div>
            <div>
              <span style={labelStyle}>stack:</span>
              <pre style={preStyle}>{stackSummary}</pre>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
