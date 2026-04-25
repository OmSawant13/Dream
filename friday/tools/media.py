"""
Media control tools — control music and volume on macOS.
"""

import subprocess
import platform

def _run_applescript(script: str):
    if platform.system() != "Darwin":
        return "Media control is currently only available on macOS, boss."
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except Exception as e:
        return f"Media protocol error: {str(e)}"

def set_volume(level: int) -> str:
    """
    Set the system volume level (0-100).
    """
    result = _run_applescript(f"set volume output volume {level}")
    if result is True:
        return f"Volume adjusted to {level} percent, boss."
    return result

def open_application(app_name: str) -> str:
    """
    Launch a local application by name (e.g., 'Spotify', 'Terminal', 'Discord').
    """
    script = f'tell application "{app_name}" to activate'
    result = _run_applescript(script)
    if result is True:
        return f"Opening {app_name} now, boss. Bringing it to the foreground."
    return result

def media_control(action: str, target_app: str = "Spotify") -> str:
    """
    Control media playback. 
    Actions: 'play', 'pause', 'next', 'previous'.
    Target Apps: 'Spotify' (default), 'Music' (Apple Music).
    """
    scripts = {
        "play": f'tell application "{target_app}" to play',
        "pause": f'tell application "{target_app}" to pause',
        "next": f'tell application "{target_app}" to next track',
        "previous": f'tell application "{target_app}" to previous track',
        "toggle": f'tell application "{target_app}" to playpause'
    }
    
    script = scripts.get(action.lower())
    if not script:
        key_codes = {"play": "key code 16", "pause": "key code 16", "next": "key code 19", "previous": "key code 18"}
        script = f'tell application "System Events" to {key_codes.get(action.lower(), "key code 16")}'

    result = _run_applescript(script)
    if result is True:
        return f"Affirmative. Executing {action} on {target_app}."
    return result

def play_spotify_track(track_name: str) -> str:
    """
    Searches and plays a specific track on Spotify.
    """
    script = f'''
    tell application "Spotify"
        play track "spotify:search:{track_name}"
    end tell
    '''
    result = _run_applescript(script)
    if result is True:
        return f"Cued up '{track_name}' on Spotify. Enjoy, boss."
    return result

def register(mcp):
    @mcp.tool()
    def set_volume_tool(level: int) -> str:
        return set_volume(level)

    @mcp.tool()
    def open_application_tool(app_name: str) -> str:
        return open_application(app_name)

    @mcp.tool()
    def media_control_tool(action: str, target_app: str = "Spotify") -> str:
        return media_control(action, target_app)

    @mcp.tool()
    def play_spotify_track_tool(track_name: str) -> str:
        return play_spotify_track(track_name)
