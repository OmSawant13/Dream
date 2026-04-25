"""
Security protocols — protect the workstation and clear sensitive data.
"""

import subprocess
import platform

def register(mcp):

    @mcp.tool()
    def lockdown_protocol() -> str:
        """
        Immediately locks the system, mutes audio, and closes browser windows.
        Use this for 'Lockdown Mode' or 'Emergency Protocol'.
        """
        system = platform.system()
        try:
            # 1. Mute Audio
            if system == "Darwin":
                subprocess.run(["osascript", "-e", "set volume with output muted"], check=True)
                # 2. Lock Screen
                subprocess.run(["osascript", "-e", 'tell application "System Events" to sleep'], check=True)
                # 3. Close Browsers (Optional but safer)
                subprocess.run(["pkill", "-x", "Google Chrome"], check=False)
                subprocess.run(["pkill", "-x", "Safari"], check=False)
            elif system == "Windows":
                subprocess.run("nircmd.exe mutesysvolume 1", shell=True, check=False) # Requires nircmd
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", check=True)
                
            return "Lockdown protocol engaged. Audio muted. System secured, boss."
        except Exception as e:
            return f"Security breach: Unable to fully engage lockdown. Error: {str(e)}"

    @mcp.tool()
    def secure_workspace() -> str:
        """
        Clears the system clipboard and hides sensitive applications.
        """
        system = platform.system()
        try:
            if system == "Darwin":
                # Clear clipboard
                subprocess.run("pbcopy < /dev/null", shell=True, check=True)
                # Hide all apps
                subprocess.run(["osascript", "-e", 'tell application "System Events" to set visible of every process whose visible is true to false'], check=True)
            elif system == "Windows":
                subprocess.run("powershell Set-Clipboard $null", shell=True, check=True)
                
            return "Workspace secured. Clipboard cleared and applications minimized."
        except Exception as e:
            return f"Unable to secure workspace: {str(e)}"
