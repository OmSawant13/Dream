import os
import sys
import time
import threading
import subprocess
import speech_recognition as sr
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align

console = Console()

# --- CONFIG ---
OS_CONTACT = "om7"

# --- CORE LOGIC ---
class NexusTUI:
    def __init__(self):
        self.status = "ONLINE"
        self.last_heard = ""
        self.log = ["System Initialized...", "Awaiting command, Boss."]
        self.frame = 0
        self.is_running = True

    def add_log(self, msg):
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(self.log) > 10: self.log.pop(0)

    def open_app(self, app_name, url=None):
        self.add_log(f"Executing: Open {app_name}")
        if url: subprocess.run(["open", url])
        else: subprocess.run(["open", "-a", app_name])

    def process_command(self, text):
        text = text.lower().strip()
        self.last_heard = text
        self.status = "THINKING"
        
        if "youtube" in text:
            self.open_app("Google Chrome", "https://youtube.com")
        elif "spotify" in text:
            self.open_app("Spotify")
        elif "whatsapp" in text:
            self.add_log(f"Contacting {OS_CONTACT}...")
            subprocess.run(["open", "-a", "WhatsApp"])
        else:
            self.add_log("Searching local brain...")
        
        self.status = "ONLINE"

    def listen_loop(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                while self.is_running:
                    try:
                        audio = recognizer.listen(source, phrase_time_limit=4)
                        text = recognizer.recognize_google(audio)
                        self.process_command(text)
                    except: pass
        except Exception as e:
            self.add_log(f"Mic Error: {e}")

    def generate_reactor(self):
        # Animated ASCII Arc Reactor
        chars = ["-", "\\", "|", "/"]
        c = chars[self.frame % 4]
        self.frame += 1
        return Text(f"""
      .-------.
    .'   {c}   '.
   /     |     \\
  |   {c}--o--{c}   |
   \\     |     /
    '.   {c}   .'
      '-------'
        """, style="bold cyan")

    def make_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="upper", size=12),
            Layout(name="lower")
        )
        layout["upper"].split_row(
            Layout(name="reactor", ratio=1),
            Layout(name="status", ratio=2)
        )
        
        # Reactor Panel
        layout["reactor"].update(Panel(Align.center(self.generate_reactor()), title="ARC CORE", border_style="cyan"))
        
        # Status Panel
        status_text = Text(f"\nSTATUS: {self.status}\n\nLAST HEARD: {self.last_heard}", style="bold green" if self.status=="ONLINE" else "bold yellow")
        layout["status"].update(Panel(status_text, title="SYSTEM STATUS", border_style="blue"))
        
        # Log Panel
        log_content = "\n".join(self.log)
        layout["lower"].update(Panel(log_content, title="MISSION LOG", border_style="dim"))
        
        return layout

def start_nexus():
    # Ensure 'rich' is installed
    try:
        import rich
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "rich"])

    tui = NexusTUI()
    threading.Thread(target=tui.listen_loop, daemon=True).start()

    with Live(tui.make_layout(), refresh_per_second=10, screen=True) as live:
        try:
            while True:
                live.update(tui.make_layout())
                time.sleep(0.1)
        except KeyboardInterrupt:
            tui.is_running = False
            sys.exit()

if __name__ == "__main__":
    start_nexus()
