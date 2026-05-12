import React, { useMemo } from 'react';
import './DiagnosticsDashboard.css';

const DiagnosticsDashboard = ({ metrics, isConnected, convState }) => {
  const stats = useMemo(() => {
    if (!metrics) return null;
    return {
      stt: metrics.stt_ms || 0,
      llm_first: metrics.first_token_ms || 0,
      llm_gen: metrics.generation_ms || 0,
      tts: metrics.tts_ms || 0,
      total: metrics.total_ms || 0,
      tokens_sec: metrics.generation_ms > 0 ? ((metrics.token_count || 0) / (metrics.generation_ms / 1000)).toFixed(1) : 0,
      intent: metrics.intent || 'N/A'
    };
  }, [metrics]);

  return (
    <div className="diagnostics-dashboard">
      <div className="dashboard-header">
        <h3>SYSTEM TELEMETRY</h3>
        <div className={`status-indicator ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? 'WEBSOCKET ACTIVE' : 'DISCONNECTED'}
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <label>State</label>
          <value className="state-value">{convState.toUpperCase()}</value>
        </div>
        <div className="metric-card">
          <label>STT Latency</label>
          <value>{stats?.stt}ms</value>
        </div>
        <div className="metric-card">
          <label>First Token</label>
          <value>{stats?.llm_first}ms</value>
        </div>
        <div className="metric-card">
          <label>TTS Latency</label>
          <value>{stats?.tts}ms</value>
        </div>
        <div className="metric-card">
          <label>Total Turn</label>
          <value className="highlight">{stats?.total}ms</value>
        </div>
        <div className="metric-card">
          <label>Throughput</label>
          <value>{stats?.tokens_sec} t/s</value>
        </div>
      </div>

      <div className="intent-badge">
        INTENT: {stats?.intent}
      </div>
      
      <div className="system-logs">
        <div className="log-line">CPU: 22% | RAM: 4.2GB</div>
        <div className="log-line">Uptime: 03:58:12</div>
        <div className="log-line">Active Memories: 142</div>
      </div>
    </div>
  );
};

export default DiagnosticsDashboard;
