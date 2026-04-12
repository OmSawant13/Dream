import asyncio
import os
from dotenv import load_dotenv
from livekit.plugins import sarvam

async def main():
    load_dotenv()
    api_key = os.getenv("SARVAM_API_KEY")
    print(f"Using Key: {api_key[:10]}...")
    
    # Initialize the TTS plugin
    tts = sarvam.TTS(
        api_key=api_key,
        model="bulbul:v3",
        target_language_code="en-IN",
        speaker="shubh"
    )
    
    print("Synthesizing 'Hello'...")
    try:
        # Try to synthesize just one sentence
        stream = tts.synthesize("Hello boss, testing the voice box.")
        async for ev in stream:
            if hasattr(ev, 'frame'):
                print("SUCCESS: Received audio frame!")
                return
        print("FAILURE: Connection finished but NO FRAMES received.")
    except Exception as e:
        print(f"ERROR during synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
