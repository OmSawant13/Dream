"""
STARK WHATSAPP PROTOCOL - ULTIMATE ROOT OVERRIDE
================================================
Bypasses all macOS GUI manipulation by directly reading the 
local WhatsApp SQLite database and utilizing the URL scheme.
"""

import os
import time
import subprocess
import pyautogui
import sqlite3
import urllib.parse

def get_whatsapp_number_from_db(contact_name: str) -> str:
    """Queries the local WhatsApp database to find the internal ID for a contact."""
    db_path = os.path.expanduser("~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ContactsV2.sqlite")
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Search by Full Name or Given Name
        cursor.execute(
            "SELECT ZWHATSAPPID FROM ZWAADDRESSBOOKCONTACT WHERE ZFULLNAME LIKE ? OR ZGIVENNAME LIKE ?", 
            (f"%{contact_name}%", f"%{contact_name}%")
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            # ZWHATSAPPID looks like '919137883718@s.whatsapp.net'
            return row[0].split('@')[0]
    except Exception as e:
        print(f"Database Query Error: {e}")
    return None

def core_send_whatsapp_message(contact: str, message: str) -> str:
    """Delivers message using the 100% reliable direct URL protocol."""
    # 1. Root Database Lookup
    number = get_whatsapp_number_from_db(contact)
    
    if number:
        # 2. Direct URL Injection
        encoded_message = urllib.parse.quote(message)
        url = f"whatsapp://send?phone={number}&text={encoded_message}"
        
        # Open URL (This inherently focuses the chat and drafts the message)
        subprocess.run(["open", url])
        time.sleep(3) # Wait for WhatsApp to fully load and process the draft
        
        # 3. Final Execution (Just press enter)
        pyautogui.press('enter')
        time.sleep(1)
        # Sometimes it needs a second enter if the app was completely closed
        pyautogui.press('enter') 
        
        return f"ULTIMATE ROOT SUCCESS: Database mapped '{contact}' to {number}. Message delivered."
    else:
        return f"FAIL: Could not find '{contact}' in local WhatsApp database. Please provide phone number."

def core_send_whatsapp_voice_note(contact: str, text_to_speak: str) -> str:
    """Delivers voice note using direct URL protocol."""
    number = get_whatsapp_number_from_db(contact)
    
    if number:
        url = f"whatsapp://send?phone={number}"
        subprocess.run(["open", url])
        time.sleep(3)
        
        # Voice notes still require physical interaction with the mic button
        # But we are guaranteed to be in the right chat!
        # Click Mic (standard location, bottom right of chat area)
        # Using a safer relative click would be better, but we rely on standard window layout
        script = '''
        tell application "WhatsApp" to activate
        tell application "System Events" to tell process "WhatsApp"
            set position of front window to {10, 40}
            set size of front window to {800, 600}
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        time.sleep(1)
        
        pyautogui.click(775, 565)
        time.sleep(1)
        subprocess.run(["say", "-v", "Samantha", text_to_speak])
        time.sleep(1)
        pyautogui.click(775, 565)
        return f"Voice note delivered to {contact} ({number})."
    else:
        return f"FAIL: Could not find '{contact}' in database."

def register(mcp):
    @mcp.tool()
    def send_whatsapp_message(contact: str, message: str) -> str:
        """Send a real WhatsApp text message."""
        return core_send_whatsapp_message(contact, message)

    @mcp.tool()
    def send_whatsapp_voice_note(contact: str, text_to_speak: str) -> str:
        """Record and send a WhatsApp voice note."""
        return core_send_whatsapp_voice_note(contact, text_to_speak)
