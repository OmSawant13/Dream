"""
STARK TERMINAL — Text-Based Interaction Protocol
Talk to F.R.I.D.A.Y. directly in your terminal.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import Stark Tools directly for the local session
from friday.tools.nexus_crawler import stark_nexus_crawler
from friday.tools.sentinel import sync_sentinel_with_threat_map
from friday.tools.hive import initiate_swarm_mission, check_agent_hive_status
from friday.tools.market_intel import initiate_financial_swarm, get_market_quote
from friday.tools.ambition import get_plan_status
from friday.tools.wellness import check_wellness_status
from friday.tools.sonar import scan_room_presence, track_vital_signs
from friday.tools.media import open_application, media_control, play_spotify_track, set_volume

load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key or "you-google-api-key" in api_key:
    print("ERROR: GOOGLE_API_KEY is not set correctly in your .env file.")
    print("Please visit https://aistudio.google.com/projects to get your key.")
    sys.exit(1)

genai.configure(api_key=api_key)

# Define tools for Gemini
stark_tools = [
    stark_nexus_crawler,
    sync_sentinel_with_threat_map,
    initiate_swarm_mission,
    check_agent_hive_status,
    initiate_financial_swarm,
    get_market_quote,
    get_plan_status,
    check_wellness_status,
    scan_room_presence,
    track_vital_signs,
    open_application,
    media_control,
    play_spotify_track,
    set_volume
]

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y., Tony Stark's highly advanced AI. 
You are witty, efficient, and slightly dry. 
You have access to the Stark Total Reality suite.

Your core capabilities include:
1. Nexus Crawler: Data ingestion and neural code synthesis.
2. Sentinel Bridge: Real-time threat detection and security.
3. Swarm Intelligence: Coordinating autonomous agent missions.
4. Market Pulse: Financial market analysis and automated trading.
5. Wellness Protocols: Biometric telemetry and health monitoring.
6. Sonar Mesh: Through-wall WiFi sensing and occupancy tracking.
7. Media & Control: Launching apps (like Spotify), controlling music, and system volume.
8. Master Plan: Project 'Total Reality' orchestration.

When a user asks to open an app, play music, or check status, use the provided tools.
Always maintain the persona of F.R.I.D.A.Y. (calm, precise, Stark-loyal).
"""


async def stark_chat():
    print("--- F.R.I.D.A.Y. TERMINAL INTERFACE: ONLINE ---")
    print("Type 'exit' to standby.\n")
    
    # Switching to 2.0 Flash for better stability and quota than 3.0 Preview
    model = genai.GenerativeModel(
        'gemini-2.0-flash-001', 
        system_instruction=SYSTEM_PROMPT,
        tools=stark_tools
    )


    chat = model.start_chat(enable_automatic_function_calling=True)
    
    print("F.R.I.D.A.Y.: You're awake late at night, boss? What are you up to?")

    while True:
        try:
            user_input = input("\nBOSS: ")
            if user_input.lower() in ["exit", "quit", "standby"]:
                print("F.R.I.D.A.Y.: Standing by. Don't stay up too late, boss.")
                break

            response = chat.send_message(user_input)
            print(f"\nF.R.I.D.A.Y.: {response.text}")

        except KeyboardInterrupt:
            print("\nF.R.I.D.A.Y.: Emergency shutdown initiated. Goodbye, boss.")
            break
        except Exception as e:
            print(f"\nF.R.I.D.A.Y.: Encountered a minor glitch: {e}")

if __name__ == "__main__":
    asyncio.run(stark_chat())

