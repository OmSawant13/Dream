import subprocess
import time

def whatsapp_command(contact: str, message: str = "") -> str:
    """Opens WhatsApp and navigates to a contact. NATIVE FORCE."""
    print(f"🛠️ NATIVE TRIGGER: WhatsApp for {contact}")
    try:
        # Force open app
        subprocess.run(["open", "-a", "WhatsApp"])
        time.sleep(2)
        
        # Robust AppleScript for search
        script = f'''
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                keystroke "f" using {{command down}}
                delay 0.5
                keystroke "{contact}"
                delay 1.0
                keystroke return
                if "{message}" is not "" then
                    delay 0.5
                    keystroke "{message}"
                    delay 0.5
                    keystroke return
                end if
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        return f"WhatsApp interaction complete for {contact}."
    except Exception as e:
        print(f"❌ NATIVE ERROR: {e}")
        return f"WhatsApp Protocol Error: {e}"
