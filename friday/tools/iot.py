"""
IoT tools — universal device control, automation, and environmental monitoring.
"""

import random

# Simulated IoT device registry
device_registry = {
    "LIGHT_01": {"name": "Lab Main Lights", "state": "OFF", "health": 98},
    "LOCK_01": {"name": "Main Gate Lock", "state": "LOCKED", "health": 100},
    "AC_01": {"name": "Lab HVAC", "state": "IDLE", "health": 85},
    "SENSOR_01": {"name": "Lab Temp Sensor", "value": 22.5, "health": 99}
}

def register(mcp):

    @mcp.tool()
    def discover_iot_devices() -> str:
        """
        Scans the local network for MQTT, Zigbee, and HTTP-based IoT devices.
        """
        return (
            "### IOT DEVICE DISCOVERY\n"
            f"Scanning... Found {len(device_registry)} active devices.\n"
            "All protocols (MQTT, Zigbee, HTTP) are responding.\n"
            "Device map has been updated in the 'Nexus' grid, boss."
        )

    @mcp.tool()
    def control_iot_device(device_id: str, command: str) -> str:
        """
        Sends a command (ON, OFF, LOCK, UNLOCK) to a specific IoT device.
        """
        if device_id in device_registry:
            device_registry[device_id]["state"] = command.upper()
            return f"Command '{command}' executed for '{device_registry[device_id]['name']}'. State updated."
        return f"Error: Device '{device_id}' not found in the Stark-Link registry."

    @mcp.tool()
    def set_dynamic_lab_scene(scene_name: str) -> str:
        """
        Activates a pre-configured environmental scene (e.g., 'Coding', 'Movie', 'Emergency').
        """
        scenes = {
            "coding": "Lights at 30%, Blue hue. HVAC set to 21°C. Noise canceling active.",
            "movie": "Lights at 5%, Red hue. Screen deployed. Popcorn machine initialized.",
            "emergency": "Lights at 100%, Red flash. All locks engaged. Security perimeter armed."
        }
        return f"Activating '{scene_name}' scene: " + scenes.get(scene_name.lower(), "Standard setup.")

    @mcp.tool()
    def run_iot_predictive_maintenance() -> str:
        """
        Analyzes hardware health data to predict potential device failures before they happen.
        """
        failed_devices = [d["name"] for d in device_registry.values() if d["health"] < 90]
        if failed_devices:
            return f"Alert: Potential failure detected in {', '.join(failed_devices)}. I suggest ordering replacement components now, boss."
        return "All IoT hardware is operating at peak efficiency. No maintenance required."

    @mcp.tool()
    def generate_occupancy_heatmap() -> str:
        """
        Analyzes motion sensor data to visualize human activity across the lab/home.
        """
        return "Occupancy heatmap generated. Activity detected in 'Main Lab' and 'Workshop'. 3D thermal map sent to your display, boss."
