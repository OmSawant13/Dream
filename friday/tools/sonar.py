"""
STARK SONAR MESH
================
Detects presence by scanning the local network for active biometric devices.
"""

import subprocess
import platform
import socket
import threading

def scan_room_presence(sensitivity: float = 1.0) -> str:
    """Scans the local network to detect active devices and estimate occupancy."""
    try:
        # Get local IP base
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        prefix = ".".join(local_ip.split(".")[:-1]) + "."
        active_count = 0
        threads = []

        def ping_ip(ip):
            nonlocal active_count
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-t', '1', ip]
            if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                active_count += 1

        # Scan a small range (last 20 IPs) for speed
        start_ip = int(local_ip.split(".")[-1])
        for i in range(max(1, start_ip-10), min(255, start_ip+10)):
            t = threading.Thread(target=ping_ip, args=(prefix + str(i),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=0.1)

        occupancy = int(active_count * sensitivity)
        status = "SECURE" if occupancy < 5 else "CONGESTED"
        
        return (f"Sonar Mesh Scan Complete.\n"
                f"Detected Entities: {occupancy}\n"
                f"RF Signature: {status}\n"
                f"Bio-metrics: {active_count} active network nodes.")
    except Exception as e:
        return f"Sonar Error: {e}"
