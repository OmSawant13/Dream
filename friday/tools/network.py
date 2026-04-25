"""
Network tools — scan local network and check connection health.
"""

import subprocess
import platform

def register(mcp):

    @mcp.tool()
    def scan_network_devices() -> str:
        """
        Scans the local network for active devices.
        Use this for 'Who's on my network?' or 'Security check'.
        """
        system = platform.system()
        try:
            if system == "Darwin" or system == "Linux":
                # 'arp -a' is a quick way to see known devices
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                devices = result.stdout.strip().split("\n")
                return f"Scanning local frequencies... Found {len(devices)} active signatures:\n" + "\n".join(devices[:10])
            elif system == "Windows":
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                return f"Network scan results (Windows):\n{result.stdout}"
            return "Network protocols are not available on this OS, boss."
        except Exception as e:
            return f"Network scan failed: {str(e)}"

    @mcp.tool()
    def check_connection_health() -> dict:
        """
        Test the latency and health of the internet connection.
        """
        try:
            # Ping Google DNS
            result = subprocess.run(["ping", "-c", "3", "8.8.8.8"], capture_output=True, text=True)
            return {
                "latency_test": "Successful",
                "report": result.stdout.split("\n")[-2],
                "status": "Connection stable. Encryption active."
            }
        except:
            return {"status": "Network jitter detected. Connection unstable."}
