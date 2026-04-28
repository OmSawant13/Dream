import tkinter as tk
from tkinter import ttk
import threading
import speech_recognition as sr
import subprocess
import time
import os
import ollama as ollama_client

# --- CONFIGURATION ---
OS_CONTACT = "om7" # Your default WhatsApp contact
OLLAMA_MODEL = "llama3.2"

# --- CORE TOOLS ---
def open_app(app_name, url=None):
    print(f"🚀 Opening {app_name}...")
    if url:
        subprocess.run(["open", url])
    else:
        subprocess.run(["open", "-a", app_name])

def whatsapp(contact, msg=""):
    print(f"📲 Messaging {contact}...")
    subprocess.run(["open", "-a", "WhatsApp"])
    script = f'tell application "System Events" to tell process "WhatsApp"\nset frontmost to true\nkeystroke "f" using {{command down}}\ndelay 0.5\nkeystroke "{contact}"\ndelay 1.0\nkeystroke return\nend tell'
    subprocess.run(["osascript", "-e", script])

# --- NATIVE GUI ---
class FridayHUD:
    def __init__(self, root):
        self.root = root
        self.root.title("F.R.I.D.A.Y. CORE")
        self.root.geometry("400x600")
        self.root.configure(bg='#06080f')
        self.root.attributes('-topmost', True) # Always on top
        
        # Arc Reactor (Canvas)
        self.canvas = tk.Canvas(root, width=200, height=200, bg='#06080f', highlightthickness=0)
        self.canvas.pack(pady=40)
        self.reactor = self.canvas.create_oval(50, 50, 150, 150, outline='#00d4ff', width=4, fill='#001a22')
        
        # Status Label
        self.status_var = tk.StringVar(value="SYSTEM READY")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg='#00d4ff', bg='#06080f', font=('Orbitron', 10))
        self.status_label.pack()

        # Transcript Display
        self.transcript_label = tk.Label(root, text="", fg='#9ab8c8', bg='#06080f', font=('Inter', 10), wraplength=350)
        self.transcript_label.pack(pady=20)

        # Input Field
        self.input_field = tk.Entry(root, bg='#001a22', fg='#00d4ff', insertbackground='#00d4ff', borderwidth=0, font=('Inter', 12), justify='center')
        self.input_field.pack(pady=10, ipady=8, fill='x', padx=40)
        self.input_field.bind('<Return>', self.handle_text)

        # Start Listening Thread
        threading.Thread(target=self.listen_loop, daemon=True).start()
        self.animate_reactor()

    def animate_reactor(self):
        # Pulse effect
        self.canvas.itemconfig(self.reactor, width=6 if time.time() % 2 > 1 else 3)
        self.root.after(100, self.animate_reactor)

    def handle_text(self, event=None):
        cmd = self.input_field.get()
        self.input_field.delete(0, tk.END)
        self.process_input(cmd)

    def process_input(self, text):
        text = text.lower()
        self.transcript_label.config(text=f"BOSS: {text}")
        self.status_var.set("PROCESSING...")
        self.canvas.itemconfig(self.reactor, outline='#ff9f1a')

        # 1. Instant Direct Logic
        if "youtube" in text:
            open_app("Google Chrome", "https://youtube.com")
        elif "spotify" in text:
            open_app("Spotify")
        elif "whatsapp" in text:
            whatsapp(OS_CONTACT)
        else:
            # 2. Local Brain Fallback
            try:
                resp = ollama_client.chat(model=OLLAMA_MODEL, messages=[
                    {"role": "system", "content": "You are FRIDAY. Be witty and brief."},
                    {"role": "user", "content": text}
                ])
                print(f"FRIDAY: {resp['message']['content']}")
            except:
                pass

        self.status_var.set("SYSTEM READY")
        self.canvas.itemconfig(self.reactor, outline='#00d4ff')

    def listen_loop(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                while True:
                    try:
                        audio = recognizer.listen(source, phrase_time_limit=5)
                        text = recognizer.recognize_google(audio)
                        self.root.after(0, self.process_input, text)
                    except: pass
        except:
            self.root.after(0, self.status_var.set, "MIC ERROR")

if __name__ == "__main__":
    root = tk.Tk()
    app = FridayHUD(root)
    root.mainloop()
