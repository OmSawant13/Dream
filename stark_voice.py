"""
STARK VOICE PROTOCOL — Voice-enabled local interaction using Ollama and SpeechRecognition.
No API credits required. Runs on local silicon.
"""

import os
import sys
import asyncio
import json
import ollama
import subprocess
import speech_recognition as sr

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import Stark Tools from the main script logic
from stark_ollama import (
    available_functions, tools, SYSTEM_PROMPT, 
    whatsapp_voice_note, whatsapp_text_message, system_speak
)

def listen_to_mic():
    """Listens to the microphone and returns text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[LISTENING...]")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print("[PROCESSING...]")
            text = r.recognize_google(audio)
            print(f"BOSS: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"DEBUG: Mic error: {e}")
            return None

async def run_stark_voice():
    print("--- F.R.I.D.A.Y. VOICE PROTOCOL: ONLINE ---")
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    
    # Welcome message
    welcome = "Voice link established, boss. I'm listening. What's the mission?"
    print(f"F.R.I.D.A.Y.: {welcome}")
    subprocess.run(["say", welcome])

    while True:
        try:
            user_input = listen_to_mic()
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "standby"]:
                farewell = "Understood, boss. Standing by."
                print(f"F.R.I.D.A.Y.: {farewell}")
                subprocess.run(["say", farewell])
                break
                
            messages.append({'role': 'user', 'content': user_input})
            
            response = ollama.chat(model='llama3.2', messages=messages, tools=tools)

            if response.message.tool_calls:
                for tool in response.message.tool_calls:
                    name = tool.function.name
                    if name in available_functions:
                        print(f"DEBUG: Executing {name}...")
                        result = available_functions[name](**tool.function.arguments)
                        messages.append(response.message)
                        messages.append({'role': 'tool', 'content': str(result)})
                        
                        final = ollama.chat(model='llama3.2', messages=messages)
                        reply = final.message.content
                        print(f"\nF.R.I.D.A.Y.: {reply}")
                        subprocess.run(["say", reply])
                        messages.append(final.message)
            else:
                reply = response.message.content
                print(f"\nF.R.I.D.A.Y.: {reply}")
                subprocess.run(["say", reply])
                messages.append(response.message)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nF.R.I.D.A.Y.: Glitch: {e}")

if __name__ == "__main__":
    asyncio.run(run_stark_voice())
