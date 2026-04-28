import webview
import subprocess
import time
import os
import signal
import sys

def kill_on_port(port):
    try:
        # Use lsof to find the process ID on the port and kill it
        cmd = f"lsof -ti:{port} | xargs kill -9"
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        print(f"🧹 Cleared port {port}")
    except:
        pass

# 1. HARD RESET
print("🧹 Cleaning up old Nexus signatures...")
kill_on_port(9090) # Backend
kill_on_port(5173) # Frontend

# 2. START FRESH
print("🚀 Ignition: Starting Nexus Core Systems...")
core_proc = subprocess.Popen([sys.executable, "run_nexus.py"])

# Give it a healthy 10 seconds to fully stabilize
print("⏳ Initializing Neural Grid...")
time.sleep(10)

def on_closed():
    print("🛑 Shutdown: Closing HUD...")
    core_proc.terminate()
    # Final cleanup to ensure no ghost processes
    kill_on_port(9090)
    kill_on_port(5173)
    os._exit(0)

# 3. LAUNCH HUD
print("🖥️ HUD: Opening Native Interface...")
window = webview.create_window(
    'F.R.I.D.A.Y. HUD', 
    'http://localhost:5173',
    width=1100, 
    height=850,
    background_color='#000000'
)

webview.start()
on_closed()
