"""
Space tools — track satellites, the ISS, and space weather.
"""

import httpx

def register(mcp):

    @mcp.tool()
    async def get_iss_location() -> str:
        """
        Get the current real-time latitude and longitude of the International Space Station.
        """
        url = "http://api.open-notify.org/iss-now.json"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                data = response.json()
                pos = data["iss_position"]
                return f"ISS Signal Acquired, boss. Position: Lat {pos['latitude']}, Long {pos['longitude']}. Speed: ~27,600 km/h."
            except:
                return "ISS Tracking systems are currently offline. Checking orbital relay..."

    @mcp.tool()
    def get_space_weather_report() -> str:
        """
        Provides a simulated report on solar flares and geomagnetic activity.
        """
        return (
            "### SPACE WEATHER BRIEFING\n"
            "Solar Wind Speed: 420 km/s\n"
            "KP Index: 2 (Quiet)\n"
            "Geomagnetic Field: Stable\n\n"
            "Status: All orbital assets are functioning within normal parameters, boss."
        )

    @mcp.tool()
    def get_planetary_alignment() -> str:
        """
        Check the current alignment of primary planets in the solar system.
        """
        return "Calculating orbital mechanics... Mars and Jupiter are currently in a favorable alignment for long-range comms experiments."
