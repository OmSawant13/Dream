
import asyncio
import os
from dotenv import load_dotenv
from livekit.plugins import deepgram

async def test_deepgram_tts():
    load_dotenv()
    print("Testing Deepgram TTS...")
    try:
        tts = deepgram.TTS()
        print("Deepgram TTS initialized successfully.")
    except Exception as e:
        print(f"Deepgram TTS initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepgram_tts())
