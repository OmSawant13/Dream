import sys
import threading
import speech_recognition as sr
import subprocess
import time
import re
import json
import os
import requests

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, 
                             QWidget, QLineEdit, QFrame, QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QRadialGradient, QBrush, QLinearGradient

SERVER_URL = "http://localhost:8000"

class EtherealOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self._glow = 0.5
        
        self.anim = QPropertyAnimation(self, b"glow")
        self.anim.setDuration(2500)
        self.anim.setStartValue(0.4)
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
        
        grad = QRadialGradient(center, 140)
        grad.setColorAt(0, QColor(130, 70, 255, int(self._glow * 180)))
        grad.setColorAt(0.7, QColor(0, 120, 255, int(self._glow * 120)))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, 150, 150)

        core_grad = QRadialGradient(center, 65)
        core_grad.setColorAt(0, QColor(10, 5, 20, 255))
        core_grad.setColorAt(1, QColor(0, 0, 0, 255))
        painter.setBrush(core_grad)
        painter.drawEllipse(center, 65, 65)

        eye_color = QColor(255, 255, 255, 240)
        painter.setBrush(eye_color)
        painter.drawEllipse(center.x() - 18, center.y() - 5, 12, 12)
        painter.drawEllipse(center.x() + 18, center.y() - 5, 12, 12)

class MessageBubble(QLabel):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        color = "#ffffff" if is_user else "#00e5ff"
        bg = "rgba(255, 255, 255, 25)" if is_user else "rgba(0, 180, 255, 30)"
        self.setStyleSheet(f"""
            color: {color};
            background: {bg};
            border-radius: 15px;
            padding: 15px;
            font-size: 14px;
            font-family: 'Arial', sans-serif;
        """)

class EtherealHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 850)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                        stop:0 rgba(10, 0, 30, 245), 
                                        stop:1 rgba(0, 10, 40, 235));
            border-radius: 30px;
            border: 1px solid rgba(0, 212, 255, 40);
        """)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(40, 60, 40, 40)
        self.layout.setSpacing(30)

        self.orb = EtherealOrb()
        self.layout.addWidget(self.orb, alignment=Qt.AlignCenter)

        self.status = QLabel("NEURAL CORE: STANDBY")
        self.status.setStyleSheet("background: transparent; color: rgba(0, 212, 255, 200); font-size: 10px; letter-spacing: 4px; font-weight: bold; font-family: 'Arial';")
        self.layout.addWidget(self.status, alignment=Qt.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.msg_container = QWidget()
        self.msg_container.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.addStretch()
        self.scroll.setWidget(self.msg_container)
        self.layout.addWidget(self.scroll)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Direct Neural Uplink...")
        self.input_field.setStyleSheet("""
            background: rgba(255, 255, 255, 10);
            color: white;
            border: 1px solid rgba(255, 255, 255, 30);
            border-radius: 25px;
            padding: 15px 25px;
            font-size: 15px;
            font-family: 'Arial';
        """)
        self.input_field.returnPressed.connect(self.handle_input)
        self.layout.addWidget(self.input_field)

        self.sync_history()
        threading.Thread(target=self.listen_loop, daemon=True).start()
        self.input_field.setFocus()

    def speak(self, text):
        threading.Thread(target=lambda: subprocess.run(["say", "-v", "Samantha", text]), daemon=True).start()

    def sync_history(self):
        try:
            res = requests.get(f"{SERVER_URL}/history")
            if res.status_code == 200:
                for item in res.json()[-5:]:
                    self.add_message(item["content"], item["role"] == "user")
        except: pass

    def add_message(self, text, is_user):
        bubble = MessageBubble(text, is_user)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        if self.msg_layout.count() > 8:
            item = self.msg_layout.takeAt(1)
            if item.widget(): item.widget().deleteLater()

    def handle_input(self):
        cmd = self.input_field.text()
        self.input_field.clear()
        if cmd:
            self.add_message(cmd, True)
            self.status.setText("CORE PROCESSING...")
            threading.Thread(target=self.send_to_server, args=(cmd,), daemon=True).start()

    def send_to_server(self, text):
        try:
            res = requests.post(f"{SERVER_URL}/command", json={"command": text})
            if res.status_code == 200:
                data = res.json()
                QTimer.singleShot(0, lambda: self.process_response(data))
        except:
            QTimer.singleShot(0, lambda: self.status.setText("LINK FAILED"))

    def process_response(self, data):
        response = data.get("response", "")
        self.status.setText("CORE: ACTIVE")
        self.add_message(response, False)
        self.speak(response)

    def listen_loop(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            while True:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5)
                    t = recognizer.recognize_google(audio)
                    QTimer.singleShot(0, lambda text=t: self.handle_voice(text))
                except: pass
    
    def handle_voice(self, text):
        self.add_message(text, True)
        self.status.setText("VOICE DECODING...")
        self.send_to_server(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EtherealHUD()
    window.show()
    sys.exit(app.exec())
