"""
Storm tools — weather analysis and flight viability predictions.
"""

import random

def register(mcp):

    @mcp.tool()
    def analyze_local_weather(location: str = "Stark Lab") -> str:
        """
        Retrieves a detailed atmospheric report for a specific location.
        """
        temp = random.randint(15, 35)
        wind = random.randint(0, 50)
        return (
            f"### WEATHER REPORT: {location.upper()}\n"
            f"Temperature: {temp}°C\n"
            f"Wind Speed: {wind} km/h\n"
            f"Visibility: 10km (Clear)\n\n"
            f"Status: Atmospheric conditions are stable, boss."
        )

    @mcp.tool()
    def predict_storm_trajectory(storm_id: str) -> str:
        """
        Simulates the path of a storm to predict its impact on flight operations.
        """
        return f"Storm '{storm_id}' is moving NE at 25km/h. It will bypass the lab perimeter in 4 hours. No flight delays expected."

    @mcp.tool()
    def check_flight_viability(altitude_ft: int = 30000) -> str:
        """
        Checks if current conditions are safe for high-altitude suit testing.
        """
        return f"Flight viability at {altitude_ft}ft: 98%. Air density is optimal. No turbulence detected in the flight corridor, boss."
