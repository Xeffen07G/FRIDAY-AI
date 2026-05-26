import os
import sys
import json
import socket
import urllib.request
import urllib.error
import asyncio

# Ensure workspace paths are correct
WORKSPACE_DIR = r"c:\Users\sayak\Downloads\JARVIS"
sys.path.append(WORKSPACE_DIR)

from scratch.real_browser_validator import run_browser_validation

def check_port_open(port):
    """Check if a port is open and listening on IPv4 or IPv6."""
    for host in ['127.0.0.1', 'localhost', '::1']:
        try:
            # Try IPv4
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            try:
                # Try IPv6
                s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                s.settimeout(0.3)
                s.connect((host, port))
                s.close()
                return True
            except Exception:
                pass
    return False

def verify_backend_health():
    for host in ['127.0.0.1', 'localhost']:
        try:
            req = urllib.request.Request(f"http://{host}:8000/api/health/")
            req.add_header('User-Agent', 'FRIDAY-Status-Checker')
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    return True, json.loads(response.read().decode('utf-8'))
        except Exception:
            pass
    return False, {}

def main():
    backend_open = check_port_open(8000)
    frontend_open = check_port_open(5173)
    
    backend_ok = False
    backend_meta = {}
    if backend_open:
        backend_ok, backend_meta = verify_backend_health()
        
    validation_res = None
    if frontend_open:
        # Run browser-level Playwright checks
        try:
            validation_res = asyncio.run(run_browser_validation())
        except Exception as e:
            validation_res = {
                "success": False,
                "error": f"Browser validation failed to execute: {e}",
                "failing_file": "Unknown",
                "stack_trace": str(e),
                "failing_component": "Unknown",
                "probable_cause": "Playwright orchestration failure"
            }
            
    # Calculate final states based strictly on deep validation truth
    frontend_healthy = False
    websocket_healthy = False
    details = "Frontend is offline."
    
    if validation_res:
        frontend_healthy = validation_res.get("success", False)
        details = validation_res.get("details") if frontend_healthy else validation_res.get("error", "Unknown runtime crash")
        # Check if websocket status was successful in browser check
        if frontend_healthy:
            websocket_healthy = True
            
    report = {
        "pipeline_state": "HEALTHY" if (backend_ok and frontend_healthy) else "FAILED",
        "backend": {
            "status": "healthy" if backend_ok else "unreachable",
            "port": 8000,
            "version": backend_meta.get("version") if backend_ok else "unknown",
            "vdb_status": backend_meta.get("vector_db", {}).get("status") if backend_ok else "unknown"
        },
        "frontend": {
            "status": "healthy" if frontend_healthy else "failed/offline",
            "port": 5173,
            "url": "http://localhost:5173/assistant",
            "details": details
        },
        "websocket": {
            "status": "connected" if websocket_healthy else "failed/disconnected",
            "details": "Synchronized through browser test." if websocket_healthy else "Unable to establish WebSocket in browser environment."
        },
        "active_ports": [p for p in [8000, 5173] if check_port_open(p)],
        "remaining_warnings": []
    }
    
    if not backend_ok:
        report["remaining_warnings"].append("Backend process is not responding to health endpoint.")
    if not frontend_healthy:
        if not frontend_open:
            report["remaining_warnings"].append("Frontend process is not alive on port 5173.")
        else:
            report["remaining_warnings"].append(f"Frontend has runtime/rendering exceptions: {details}")
            
    # Output ONLY verified truth in a strict format
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
