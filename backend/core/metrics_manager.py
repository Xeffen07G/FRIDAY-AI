import time
import json
import os
from collections import deque
from datetime import datetime
from config.settings import settings

class MetricsManager:
    """Production-grade telemetry system for tracking realtime performance."""
    
    def __init__(self, history_size=100):
        self.history = deque(maxlen=history_size)
        self.stats_file = os.path.join(settings.RUNTIME_BASE, "logs", "metrics.jsonl")
        self._ensure_storage()
        
        # In-memory aggregates
        self.cumulative_tokens = 0
        self.total_requests = 0
        self.latencies = {
            "first_token": deque(maxlen=20),
            "total": deque(maxlen=20),
            "stt": deque(maxlen=20),
            "tts": deque(maxlen=20)
        }

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)

    def record_request(self, metrics: dict):
        """Persists and updates realtime stats."""
        metrics["timestamp"] = datetime.now().isoformat()
        self.history.append(metrics)
        self.total_requests += 1
        
        # Update rolling averages
        if "generation_ms" in metrics and "total_ms" in metrics:
            tokens = metrics.get("token_count", 0)
            self.cumulative_tokens += tokens
            
        for key in self.latencies:
            m_key = f"{key}_ms"
            if m_key in metrics:
                self.latencies[key].append(metrics[m_key])
        
        # Persist to disk
        try:
            with open(self.stats_file, "a") as f:
                f.write(json.dumps(metrics) + "\n")
        except Exception:
            pass

    def get_summary(self):
        """Returns aggregated telemetry for the diagnostics dashboard."""
        import psutil
        def avg(dq): return round(sum(dq) / len(dq), 2) if dq else 0
        
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        return {
            "avg_first_token_ms": avg(self.latencies["first_token"]),
            "avg_total_latency_ms": avg(self.latencies["total"]),
            "avg_stt_ms": avg(self.latencies["stt"]),
            "avg_tts_ms": avg(self.latencies["tts"]),
            "total_requests": self.total_requests,
            "cumulative_tokens": self.cumulative_tokens,
            "uptime_seconds": int(time.time() - getattr(self, '_start_time', time.time())),
            "system_cpu": cpu,
            "system_ram": ram
        }

metrics_manager = MetricsManager()
metrics_manager._start_time = time.time()
