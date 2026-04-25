import sys
import threading
import speech_recognition as sr
import subprocess
import time
import re
import webbrowser
import json
import os
import shutil

try:
    import ollama
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "ollama", "--break-system-packages"])
    import ollama

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, 
                             QWidget, QLineEdit, QFrame, QScrollArea, QHBoxLayout, QGridLayout)
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QRadialGradient

HISTORY_FILE = "friday_history.json"

class ArcReactorCore(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._glow = 0.5
        self.anim = QPropertyAnimation(self, b"glow")
        self.anim.setDuration(1500)
        self.anim.setStartValue(0.3)
        self.anim.setEndValue(0.9)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

    @Property(float)
    def glow(self): return self._glow
    @glow.setter
    def glow(self, val):
        self._glow = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        radius = 80
        pen = QPen(QColor(0, 212, 255, int(self._glow * 255)))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(center, radius, radius)
        grad = QRadialGradient(center, radius-20)
        grad.setColorAt(0, QColor(0, 212, 255, int(self._glow * 200)))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius-10, radius-10)

class HoloPanel(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: rgba(0, 20, 30, 160); border: 1px solid #00d4ff44; border-radius: 15px;")
        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #00d4ff; font-size: 8px; letter-spacing: 2px; font-weight: bold;")
        layout.addWidget(self.title_label)
        self.content = QVBoxLayout()
        layout.addLayout(self.content)

class FridayQtHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(800, 500)
        self.history = self.load_history()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QGridLayout(self.central_widget)
        
        self.vitals_panel = HoloPanel("SYSTEM VITALS")
        self.batt_label = QLabel("BATTERY: SCANNING...")
        self.cpu_label = QLabel("CPU: SCANNING...")
        self.ip_label = QLabel("IP: LOCALHOST")
        self.vitals_panel.content.addWidget(self.batt_label)
        self.vitals_panel.content.addWidget(self.cpu_label)
        self.vitals_panel.content.addWidget(self.ip_label)
        for lbl in [self.batt_label, self.cpu_label, self.ip_label]:
            lbl.setStyleSheet("color: #9ab8c8; font-family: 'Arial'; font-size: 11px;")
        self.main_layout.addWidget(self.vitals_panel, 0, 0, 1, 1)

        self.core = ArcReactorCore()
        self.main_layout.addWidget(self.core, 0, 1, 1, 1, alignment=Qt.AlignCenter)

        self.log_panel = HoloPanel("MISSION LOG")
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.addStretch()
        self.scroll.setWidget(self.log_container)
        self.log_panel.content.addWidget(self.scroll)
        self.main_layout.addWidget(self.log_panel, 0, 2, 1, 1)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("> COMMAND F.R.I.D.A.Y. (GO TO URL / GOOGLE IT)")
        self.input_field.setStyleSheet("background: rgba(0, 10, 20, 220); color: #00d4ff; border: 1px solid #00d4ff88; border-radius: 10px; padding: 10px;")
        self.input_field.returnPressed.connect(self.handle_input)
        self.main_layout.addWidget(self.input_field, 1, 0, 1, 3)

        self.load_logs()
        threading.Thread(target=self.listen_loop, daemon=True).start()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(2000)

    def speak(self, text):
        threading.Thread(target=lambda: subprocess.run(["say", "-v", "Samantha", text]), daemon=True).start()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    return [{"role": "user" if i.get("sender") == "BOSS" or i.get("role") == "user" else "assistant", "content": i.get("text") or i.get("content") or ""} for i in data]
            except: return []
        return []

    def load_logs(self):
        for item in self.history:
            self.add_log_entry(item["content"], "BOSS" if item["role"] == "user" else "FRIDAY")

    def add_log_entry(self, text, sender):
        label = QLabel(f"[{sender}] {text}")
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {'#00d4ff' if sender == 'BOSS' else '#9ab8c8'}; font-size: 10px; margin-bottom: 5px;")
        self.log_layout.insertWidget(self.log_layout.count() - 1, label)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def refresh_stats(self):
        try:
            battery = subprocess.check_output(["pmset", "-g", "batt"]).decode()
            batt_pct = re.search(r"(\d+)%", battery).group(1)
            usage = os.getloadavg()[0]
            self.batt_label.setText(f"BATTERY: {batt_pct}%")
            self.cpu_label.setText(f"CPU LOAD: {usage:.1f}")
        except: pass
        self.input_field.setFocus()

    def handle_input(self):
        cmd = self.input_field.text()
        self.input_field.clear()
        if cmd:
            self.add_log_entry(cmd, "BOSS")
            self.save_to_history("BOSS", cmd)
            self.process_command(cmd)

    def save_to_history(self, sender, text):
        self.history.append({"role": "user" if sender == "BOSS" else "assistant", "content": text})
        if len(self.history) > 20: self.history.pop(0)
        with open(HISTORY_FILE, "w") as f: json.dump(self.history, f)

    def process_command(self, text):
        raw_text = text.lower()
        
        # SEARCH AND NAVIGATION
        if any(kw in raw_text for kw in ["google", "search", "find", "who is", "what is"]):
            query = raw_text.replace("google", "").replace("search", "").replace("find", "").replace("for", "").strip()
            self.add_log_entry(f"UPLINKING TO GOOGLE: {query}", "SYSTEM")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            self.finalize_response(f"Searching Google for {query}. Data retrieved in new tab.")
            return

        if "open" in raw_text:
            site = raw_text.replace("open", "").strip()
            if "." not in site: site += ".com"
            webbrowser.open(f"https://{site}")
            self.finalize_response(f"Opening {site}. Access granted.")
            return

        # MESSAGING
        if any(kw in raw_text for kw in ["whatsapp", "message", "say", "send"]):
            if " to " in raw_text:
                parts = raw_text.split(" to ")
                contact = parts[1].split(" on ")[0].strip()
                msg = parts[0].replace("say", "").replace("send", "").strip()
                threading.Thread(target=self.whatsapp_automate, args=(contact, msg), daemon=True).start()
                return

        threading.Thread(target=self.brain_query, args=(text,), daemon=True).start()

    def brain_query(self, text):
        try:
            messages = [{"role": "system", "content": "You are FRIDAY. Be brief and Stark-like."}]
            messages.extend(self.history[-10:])
            response = ollama.chat(model='llama3.2', messages=messages)
            ans = response['message']['content']
            QTimer.singleShot(0, lambda: self.finalize_response(ans))
        except: self.add_log_entry("LOCAL BRAIN OFFLINE.", "ERROR")

    def whatsapp_automate(self, contact, message):
        script = f'''
        tell application "WhatsApp" to activate
        delay 1.0
        tell application "System Events"
            keystroke "f" using {{command down}}
            delay 0.5
            keystroke "{contact}"
            delay 2.0
            keystroke return
            delay 1.0
            keystroke "{message}"
            delay 0.5
            keystroke return
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

    def finalize_response(self, text):
        self.add_log_entry(text, "FRIDAY")
        self.save_to_history("FRIDAY", text)
        self.speak(text)

    def listen_loop(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            while True:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5)
                    t = recognizer.recognize_google(audio)
                    QTimer.singleShot(0, lambda text=t: self.add_log_entry(text, "BOSS") or self.process_command(text))
                except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FridayQtHUD()
    window.show()
    sys.exit(app.exec())
