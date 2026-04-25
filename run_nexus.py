import subprocess
import os
import sys
import time
import signal

def kill_port(port):
    """Kills any process running on the specified port."""
    try:
        cmd = f"lsof -t -i:{port}"
        pids = subprocess.check_output(cmd, shell=True).decode().split()
        for pid in pids:
            os.kill(int(pid), signal.SIGTERM)
            print(f"🧹 Cleared old process on port {port}")
    except:
        pass

def run():
    print("🚀 F.R.I.D.A.Y. NEXUS PROTOCOL — ACTIVATING")
    
    # 0. Clean the grid
    kill_port(9090)
    kill_port(5173)
    
    # 1. Install Backend Deps
    print("📦 Checking neural dependencies...")
    deps = ["fastapi", "uvicorn", "websockets", "psutil", "google-generativeai", "ollama", "pillow", "httpx"]
    try:
        subprocess.run(["uv", "pip", "install"] + deps, check=True)
    except:
        subprocess.run([sys.executable, "-m", "pip", "install"] + deps, check=True)
    
    # 2. Start Backend & Frontend
    print("⚡ Launching NEXUS Core...")
    backend_dir = os.path.join(os.getcwd(), "nexus", "backend")
    backend_proc = subprocess.Popen([sys.executable, "server.py"], cwd=backend_dir)
    
    frontend_dir = os.path.join(os.getcwd(), "nexus", "frontend")
    print("🌐 Dashboard starting at http://localhost:5173")
    try:
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n🛑 NEXUS Protocol — STANDBY.")
        backend_proc.terminate()

if __name__ == "__main__":
    run()
