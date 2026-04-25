"""
STARK OFFLINE PROTOCOL — Local command execution without API credits.
Use this to control the system when the neural matrix is offline.
"""

import os
import sys
import asyncio

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import Stark Tools
from friday.tools.wellness import check_wellness_status
from friday.tools.sonar import scan_room_presence, track_vital_signs
from friday.tools.media import open_application, media_control, play_spotify_track, set_volume
from friday.tools.nexus_crawler import stark_nexus_crawler

def process_command(cmd):
    cmd = cmd.lower()
    
    # Media Controls
    if "spotify" in cmd:
        if "open" in cmd: return open_application("Spotify")
        if "play" in cmd:
            track = cmd.replace("play", "").replace("on spotify", "").strip()
            if not track: return media_control("play", "Spotify")
            return play_spotify_track(track)
        if "pause" in cmd: return media_control("pause", "Spotify")
        if "next" in cmd: return media_control("next", "Spotify")
    
    # System Controls
    if "volume" in cmd:
        try:
            level = int(''.join(filter(str.isdigit, cmd)))
            return set_volume(level)
        except: return "Please specify a volume level, boss."
        
    # Health & Sensing
    if "wellness" in cmd or "health" in cmd: return check_wellness_status()
    if "sonar" in cmd or "presence" in cmd: return scan_room_presence()
    if "vital" in cmd or "heart" in cmd: return track_vital_signs()
    
    # Crawler
    if "crawl" in cmd or "blueprint" in cmd:
        return stark_nexus_crawler("blueprint_extraction", "STARK-OS-KERNEL")

    if "help" in cmd:
        return "Capabilities: Spotify (open/play/pause/next), Volume [0-100], Wellness, Sonar, Vitals, Crawler."

    return "Command not recognized in offline mode. Type 'help' for available protocols, boss."

async def main():
    print("--- F.R.I.D.A.Y. OFFLINE PROTOCOL: ACTIVE ---")
    print("Neural Matrix is offline. Local command execution only.")
    print("Type 'exit' to standby.\n")
    
    print("F.R.I.D.A.Y.: Standing by on local reserves, boss. What do you need?")

    while True:
        try:
            user_input = input("\nBOSS (Offline): ")
            if user_input.lower() in ["exit", "quit"]:
                print("F.R.I.D.A.Y.: Powering down local reserves. Goodbye.")
                break

            response = process_command(user_input)
            print(f"\nF.R.I.D.A.Y.: {response}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nF.R.I.D.A.Y.: Local error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
