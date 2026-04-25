"""
STARK WHATSAPP PROTOCOL
========================
Advanced UI automation for WhatsApp delivery on macOS.
Uses Visual Calibration and Spiral-Striking.
"""

import os
import time
import math
import subprocess
import pyautogui

def _find_mic_visually():
    """Scans bottom-right corner for the WhatsApp mic icon."""
    sw, sh = pyautogui.size()
    img = pyautogui.screenshot(region=(sw-150, sh-150, 150, 150))
    for x in range(149, 0, -5):
        for y in range(149, 0, -5):
            r, g, b = img.getpixel((x, y))[:3]
            # WhatsApp Green or Mic Gray
            if (g > 100 and g > r*1.6 and g > b*1.3) or \
               (abs(r-84) < 8 and abs(g-101) < 8 and abs(b-111) < 8):
                return (sw - 150 + x), (sh - 150 + y)
    return None

def _calibrate_window():
    """Forces WhatsApp to 0,0 and standard size."""
    script = ('tell application "System Events" to tell process "WhatsApp" to try\n'
              'set frontmost to true\n'
              'set position of front window to {0, 0}\n'
              'set size of front window to {800, 600}\n'
              'end try')
    subprocess.run(["osascript", "-e", script])
    time.sleep(1.0)

def send_whatsapp_message(contact: str, message: str) -> str:
    """Sends a text message to a contact."""
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(2.0)
    _calibrate_window()
    
    script = f'''
    tell application "System Events"
        tell process "WhatsApp"
            set frontmost to true
            keystroke "f" using {{command down}} -- Search
            delay 0.5
            keystroke "a" using {{command down}}
            keystroke (ASCII character 8) -- Backspace
            delay 0.5
            keystroke "{contact}"
            delay 2.0
            key code 125 -- Down arrow
            delay 0.5
            key code 36 -- Enter
            delay 1.0
            keystroke "{message}"
            delay 0.5
            key code 36 -- Enter
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    return f"Message sent to {contact}."

def send_whatsapp_voice_note(contact: str, text_to_speak: str) -> str:
    """Sends a voice note by speaking text aloud during recording."""
    target_num = contact.strip().replace(" ", "").replace("-", "")
    subprocess.run(["open", f"whatsapp://send?phone={target_num}"])
    time.sleep(4.0)
    _calibrate_window()

    loc = _find_mic_visually() or (775, 565)
    mx, my = loc
    pyautogui.moveTo(mx, my, duration=0.3)
    pyautogui.click()
    time.sleep(1.0)

    # Spiral search if mic didn't trigger
    if _find_mic_visually():
        for radius in range(5, 40, 8):
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                pyautogui.click(mx + int(radius * math.cos(rad)),
                                my + int(radius * math.sin(rad)))
            if not _find_mic_visually(): break

    # Speak the voice note
    subprocess.run(["say", "-v", "Samantha", text_to_speak])
    time.sleep(1.0)

    # Stop recording
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.press('enter')
    return f"Voice note sent to {contact}."
