import subprocess

def play_entertainment(platform: str, query: str = "") -> str:
    """Plays music or videos on Spotify or YouTube. FORCED NATIVE."""
    print(f"🛠️ NATIVE TRIGGER: Opening {platform} with query: {query}")
    try:
        if "spotify" in platform.lower():
            # Force open Spotify app
            subprocess.run(["open", "-a", "Spotify"])
            if query:
                # Use Spotify's search protocol
                subprocess.run(["open", f"spotify:search:{query}"])
            return f"Spotify protocol activated for {query}."
                
        elif "youtube" in platform.lower():
            url = f"https://www.youtube.com/results?search_query={query}" if query else "https://www.youtube.com"
            # Force open in default browser
            subprocess.run(["open", url])
            return f"YouTube bridge established."
            
        return "Target not identified in entertainment database."
    except Exception as e:
        print(f"❌ NATIVE ERROR: {e}")
        return f"System Error: {e}"
