"""
STARK OLLAMA PROTOCOL — Mark XXXIV: Absolute Zero
Final hard-coded targeting for standard Mac WhatsApp resolution.
"""

import os
import sys
import asyncio
import json
import ollama
import subprocess
import time
import re
import pyautogui
import pyperclip

# STARK OVERRIDE: Pro settings
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = False 

def clean_text(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r'["\'\{\}\[\]]', '', text)
    if any(x in text.lower() for x in ["friday", "frida", "system"]): return "Om Sawant"
    return text.strip()

def execute_voice_note(contact, message):
    target_num = contact.strip().replace(" ", "").replace("-", "")
    
    # 1. DEEP LINK
    if re.search(r'\d{10,}', target_num):
        print(f"DEBUG: [STRIKE] Deep-linking to {target_num}...")
        subprocess.run(["open", f"whatsapp://send?phone={target_num}"])
    else:
        subprocess.run(["open", "-a", "WhatsApp"])
        time.sleep(1.0)
        pyautogui.hotkey('command', 'f')
        pyperclip.copy(contact)
        pyautogui.hotkey('command', 'v')
        pyautogui.press('enter')
    
    time.sleep(4.0) # Maximum wait for UI load
    
    # 2. ABSOLUTE ZERO TARGETING (Hard-coded for typical Mac Retina)
    # On a 1440x900 (2880x1800 retina) screen, the mic is around:
    # Points: 1405, 835
    # Pixels: 2810, 1670
    
    sw, sh = pyautogui.size()
    print(f"DEBUG: [SCAN] Screen Size: {sw}x{sh}")
    
    # Smart Fallback
    mx, my = sw - 35, sh - 65
    
    print(f"DEBUG: [LOCK] Absolute Zero at ({mx}, {my})")
    
    # 3. PRO GLIDE
    pyautogui.moveTo(mx, my, duration=1.5, tween=pyautogui.easeInOutQuad)
    time.sleep(0.5)
    
    # 4. SATURATION CLICKING (The Grid)
    print("DEBUG: [SWEEP] Saturating area with clicks...")
    for dx in [-20, 0, 20]:
        for dy in [-20, 0, 20]:
            pyautogui.click(mx + dx, my + dy)
            time.sleep(0.1)
    
    # 5. SPEAK
    voice_msg = "आप कौन हैं?" if "who are you" in message.lower() else "सिस्टम चेक।"
    subprocess.run(["say", "-v", "Lekha", voice_msg])
    time.sleep(2.5)
    
    # 6. SEND
    pyautogui.click(mx, my)
    time.sleep(0.3)
    pyautogui.press('enter')
    return True

async def run():
    print("\n" + "="*50)
    print("--- F.R.I.D.A.Y. OLLAMA PROTOCOL: ONLINE (MARK XXXIV) ---")
    print("="*50 + "\n")
    
    msgs = [{'role': 'system', 'content': "You are F.R.I.D.A.Y. Respond ONLY with VOICE: [Name] | [Message]"}]
    
    while True:
        try:
            cmd = input("\nBOSS: ")
            if not cmd: continue
            msgs.append({'role': 'user', 'content': cmd})
            
            res = ollama.chat(model='llama3.2', messages=msgs)
            content = res.message.content
            
            if "VOICE:" in content or any(w in content.lower() for w in ["can't", "sorry", "policy"]):
                num_match = re.search(r'\+?\d[\d\s-]{8,}', cmd)
                target = num_match.group(0) if num_match else "Om Sawant"
                execute_voice_note(target, cmd)
                print("F.R.I.D.A.Y.: Mission Accomplished.")
            else:
                print(f"F.R.I.D.A.Y.: {content}")
                msgs.append(res.message)
        except KeyboardInterrupt: break
        except Exception as e: print(f"GLITCH: {e}")

if __name__ == "__main__":
    asyncio.run(run())
