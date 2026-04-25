"""
Host control tools — interact with the operating system (Mac/Windows).
"""

import os
import subprocess
import platform
from datetime import datetime

def register(mcp):

    @mcp.tool()
    def open_application(app_name: str) -> str:
        """
        Opens a specific application on the host machine.
        Example: 'Spotify', 'Visual Studio Code', 'Discord'.
        """
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-a", app_name], check=True)
            elif system == "Windows":
                # Attempt to start the app via shell
                subprocess.run(f"start {app_name}", shell=True, check=True)
            else:
                return f"I'm not currently configured to control {system} applications, boss."
                
            return f"Initializing {app_name} now. It should be on your screen momentarily."
        except Exception as e:
            return f"I couldn't find {app_name} in the system archives, boss. Error: {str(e)}"

    @mcp.tool()
    def take_screenshot() -> str:
        """
        Capture a screenshot of the primary display.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        system = platform.system()
        
        try:
            if system == "Darwin":
                subprocess.run(["screencapture", filename], check=True)
            elif system == "Windows":
                # Requires powershell snippet or external tool; skipping for now or using a generic message
                return "Screen capture on Windows requires additional security clearance, boss. I'm working on it."
            else:
                return f"I cannot capture visuals on {system} yet."
                
            return f"Visual data captured and saved as {filename}, boss."
        except Exception as e:
            return f"Screenshot protocol failed: {str(e)}"

    @mcp.tool()
    def get_system_diagnostics() -> dict:
        """
        Returns a detailed report of system performance (CPU, Memory, Disk).
        """
        import psutil
        
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_load": f"{cpu_usage}%",
            "memory_usage": f"{memory.percent}%",
            "available_memory": f"{memory.available // (1024**2)} MB",
            "disk_free": f"{disk.free // (1024**3)} GB",
            "status": "All systems nominal" if cpu_usage < 80 else "Systems under heavy load"
        }

    @mcp.tool()
    def list_files(directory: str = ".") -> str:
        """
        List files in a specific directory. Defaults to the current project directory.
        """
        try:
            files = os.listdir(directory)
            # Filter out hidden files
            visible_files = [f for f in files if not f.startswith(".")]
            return f"Found {len(visible_files)} items in {os.path.abspath(directory)}:\n" + "\n".join(visible_files[:20])
        except Exception as e:
            return f"Unable to access the file grid: {str(e)}"
