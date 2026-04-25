import httpx

def get_weather(city: str) -> str:
    """Fetches real-time weather information for any city."""
    try:
        # Use wttr.in for quick, keyless weather data
        url = f"https://wttr.in/{city}?format=%C+%t+with+humidity+of+%h"
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 200:
            return f"Current conditions in {city}: {resp.text}. What's the next move, boss?"
        else:
            return "My weather sensors are temporarily offline. Might be solar flares."
    except Exception as e:
        return f"Weather Error: {e}"
