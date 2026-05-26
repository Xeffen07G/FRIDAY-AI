import os
import sys
import time
import socket
import urllib.request
import urllib.error
import subprocess
import webbrowser
import json
import asyncio
import shutil

# Ensure workspace paths are correct
WORKSPACE_DIR = r"c:\Users\sayak\Downloads\JARVIS"
sys.path.append(WORKSPACE_DIR)

from scratch.real_browser_validator import run_browser_validation

def kill_process_on_port(port):
    """Find and kill any process listening on the specified port on Windows."""
    try:
        cmd = f"netstat -ano | findstr :{port}"
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        pids = set()
        for line in out.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in parts:
                pids.add(parts[-1])
        
        for pid in pids:
            if pid and pid != "0":
                print(f"Port {port} is occupied by PID {pid}. Terminating...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.5)
    except Exception:
        pass

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
    """Poll backend health API."""
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/health/")
        req.add_header('User-Agent', 'FRIDAY-Boot-Orchestrator')
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("status") == "healthy":
                    return True, data
    except Exception as e:
        return False, str(e)
    return False, "Non-200 status code"

def start_backend():
    print("Launching F.R.I.D.A.Y. Core Backend (Port 8000)...")
    backend_dir = os.path.join(WORKSPACE_DIR, "backend")
    python_exe = os.path.join(WORKSPACE_DIR, ".venv", "Scripts", "python.exe")
    
    # Spawn as background process
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "main:app", "--port", "8000", "--host", "127.0.0.1"],
        cwd=backend_dir
    )

def start_frontend():
    print("Launching Vite Frontend (Port 5173)...")
    frontend_dir = os.path.join(WORKSPACE_DIR, "frontend")
    
    # Spawn npm batch command
    return subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=frontend_dir
    )

def trigger_frontend_recovery():
    print("\n--- FRONTEND RECOVERY MODE TRIGGERED ---")
    print("Stopping current Vite process...")
    kill_process_on_port(5173)
    # Aggressively kill node.exe as well
    subprocess.run("taskkill /F /IM node.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    
    # Clear stale Vite cache
    vite_cache_dir = os.path.join(WORKSPACE_DIR, "frontend", "node_modules", ".vite")
    if os.path.exists(vite_cache_dir):
        print(f"Clearing stale Vite cache at: {vite_cache_dir}")
        try:
            shutil.rmtree(vite_cache_dir)
            print("Vite cache cleared successfully.")
        except Exception as e:
            print(f"Warning: Could not clear Vite cache: {e}")
    else:
        print("Vite cache directory not found. No stale cache to clear.")
        
    print("Restarting Vite frontend cleanly...")
    proc = start_frontend()
    time.sleep(3.0)
    return proc

def run_pipeline():
    # 1. STARTING
    print("\n[Stage 1/7] STARTING: Resolving port conflicts and system boot...")
    kill_process_on_port(8000)
    kill_process_on_port(5173)
    
    # Ensure they are truly clean
    if check_port_open(8000) or check_port_open(5173):
        print("Aggressive cleanup required for orphaned processes...")
        subprocess.run("taskkill /F /IM uvicorn.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /F /IM node.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        
    # 2. PROCESS_RUNNING
    print("\n[Stage 2/7] PROCESS_RUNNING: Launching background processes...")
    backend_proc = start_backend()
    frontend_proc = start_frontend()
    
    # Wait for processes to open ports
    backend_started = False
    frontend_started = False
    
    for i in range(40):
        time.sleep(0.5)
        if not backend_started and check_port_open(8000):
            backend_started = True
            print("Backend TCP port 8000 is open.")
        if not frontend_started and check_port_open(5173):
            frontend_started = True
            print("Frontend TCP port 5173 is open.")
        if backend_started and frontend_started:
            break
            
    if not (backend_started and frontend_started):
        print("\nERROR: Failed to establish baseline process states.")
        print(f"Backend started: {backend_started}, Frontend started: {frontend_started}")
        return False, {"error": "Baseline process startup failed"}

    # Poll backend health endpoint to confirm API service ready
    backend_ready = False
    for _ in range(30):
        ok, _ = verify_backend_health()
        if ok:
            backend_ready = True
            print("Backend health endpoint responds: OK")
            break
        time.sleep(0.5)
        
    if not backend_ready:
        print("\nERROR: Backend processes are running but health check endpoint failed.")
        return False, {"error": "Backend API health check failed"}

    # 3. PAGE_RENDER_CHECK, 4. WEBSOCKET_CHECK, 5. CONSOLE_ERROR_AUDIT, 6. UI_INTERACTION_CHECK
    # We call our Playwright-based browser validator to check all of these
    print("\n[Stage 3-6/7] BROWSER VALIDATION: Booting automated Playwright audit...")
    validation_res = asyncio.run(run_browser_validation())
    
    # If failed, trigger recovery mode once!
    if not validation_res["success"]:
        print(f"\nBrowser validation failed on first attempt: {validation_res.get('error')}")
        
        # Trigger Frontend Recovery Mode
        trigger_frontend_recovery()
        
        # Wait for port 5173 to be back online
        for _ in range(30):
            if check_port_open(5173):
                break
            time.sleep(0.5)
            
        print("\nRetrying browser validation after recovery action...")
        validation_res = asyncio.run(run_browser_validation())

    if not validation_res["success"]:
        # 5. FAILURE REPORTING
        print("\n--- FAILURE REPORT ---")
        print(f"CRITICAL ERROR DETECTED DURING STARTUP!")
        print(f"Exact File: {validation_res.get('failing_file')}")
        print(f"Exact Failing Component: {validation_res.get('failing_component')}")
        print(f"Exact Probable Cause: {validation_res.get('probable_cause')}")
        print(f"Exact Stack Trace:\n{validation_res.get('stack_trace')}")
        print("----------------------")
        return False, validation_res

    # 7. HEALTHY
    print("\n[Stage 7/7] HEALTHY: All verification checks passed.")
    print("Declaring frontend and backend fully operational.")
    return True, validation_res

def main():
    print("==============================================")
    print("=== F.R.I.D.A.Y. STRICT BOOT ORCHESTRATOR ===")
    print("==============================================")
    start_time = time.time()
    
    success, result = run_pipeline()
    
    latency = round(time.time() - start_time, 2)
    
    # Prepare reports
    report = {
        "pipeline_state": "HEALTHY" if success else "FAILED",
        "startup_latency_seconds": latency,
        "backend": {
            "status": "healthy" if success else "unhealthy",
            "port": 8000,
            "url": "http://localhost:8000"
        },
        "frontend": {
            "status": "healthy" if success else "failed",
            "port": 5173,
            "url": "http://localhost:5173/assistant"
        },
        "browser_validation": result
    }
    
    # Strictly check truthfulness rule
    # Never print "verified", "operational", "healthy", "successful" unless it actually passed!
    if success:
        print("\n=== SYSTEM INITIATED SUCCESSFULLY ===")
        print("All automated UI validation checks passed in the browser environment.")
        print(f"System latency: {latency}s")
        print(json.dumps(report, indent=2))
        
        # Open browser to assistant console
        print("\nLaunching user browser session...")
        webbrowser.open("http://localhost:5173/assistant")
    else:
        print("\n=== SYSTEM BOOT SEQUENCING FAILED ===")
        print("The system is in a degraded or broken state.")
        print(json.dumps(report, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
