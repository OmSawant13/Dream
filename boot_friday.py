import subprocess
import sys
import os
import time
import requests
import socket

# --- SYSTEM SETTINGS ---
VERSION = "17.1-STARK-CORE"
PORT = 8000
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
SERVER_PATH = os.path.join(BACKEND_DIR, "unified_server.py")
HUD_PATH = os.path.join(BACKEND_DIR, "nexus_qt.py")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def boot():
    print(f"\n🚀 IGNITING F.R.I.D.A.Y. ARCHITECTURE [{VERSION}]")
    print("═"*50)

    # 1. Start Server if not running
    if is_port_in_use(PORT):
        print(f"🛰️  [STARK-CORE] Neural Core detected on port {PORT}. Reusing uplink.")
        server_proc = None
    else:
        print(f"🔥 [STARK-CORE] Igniting Neural Core (Unified Server)...")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        server_proc = subprocess.Popen(["uv", "run", "python3", SERVER_PATH], env=env)
        
        # Wait for ready
        retries = 15
        while retries > 0:
            try:
                res = requests.get(f"http://localhost:{PORT}/")
                if res.status_code == 200:
                    print(f"✅ [STARK-CORE] Neural Core is ONLINE.")
                    break
            except:
                time.sleep(1)
                retries -= 1
        
        if retries == 0:
            print("❌ [STARK-CORE] Ignition failed. Check Ollama or Port conflicts.")
            if server_proc: server_proc.terminate()
            return

    # 2. Launch HUD
    try:
        # Launch HUD in the background so it doesn't block the terminal
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        subprocess.Popen(["uv", "run", "python3", HUD_PATH], env=env)
        print(f"✅ [STARK-HUD] Holographic Interface active in background.")
        print(f"\n🚀 F.R.I.D.A.Y. IS READY, BOSS.")
        print(f"   - Web HUD: http://localhost:8000")
        print(f"   - Floating HUD: Active")
        print(f"   - Nexus Protocol: Online")
        
        # Keep the script alive or wait for user to exit
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 [STARK-CORE] Boss requested standby. Powering down...")
    finally:
        if server_proc:
            print("💤 [STARK-CORE] Moving Neural Core to background sleep...")
            # server_proc.terminate()

if __name__ == "__main__":
    boot()
