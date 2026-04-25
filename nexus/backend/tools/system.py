import os
import subprocess
import psutil
import platform
from datetime import datetime

def get_system_diagnostics() -> str:
    """Get REAL system stats: CPU, RAM, disk, battery."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    battery_status = "N/A"
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery:
            battery_status = f"{battery.percent}% {'(Charging)' if battery.power_plugged else '(Discharging)'}"
            
    return f"Status: CPU {cpu}%, RAM {ram}%, Disk {disk}%, Battery {battery_status}."

def open_application(app_name: str) -> str:
    """Opens a macOS application by name."""
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return f"Successfully opened {app_name}, boss."
    except Exception:
        return f"Couldn't find {app_name} in the local grid."

def run_terminal_command(command: str) -> str:
    """Executes a shell command on the host system."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return f"Output: {result.stdout if result.stdout else result.stderr}"
    except Exception as e:
        return f"Execution error: {e}"
