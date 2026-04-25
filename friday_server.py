"""
F.R.I.D.A.Y. Voice Interface Server
=====================================
WebSocket backend for the voice UI.
Connects the browser-based clap/voice interface to the FRIDAY brain.

Run:  uv run python3 friday_server.py
"""

import asyncio
import json
import os
import subprocess
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

import websockets

# Import brain components from stark_final
from stark_final import (
    ALL_TOOLS, SYSTEM_PROMPT, TOOL_MAP,
    _build_ollama_tools, _ollama_chat,
    LLM_PROVIDER, GEMINI_MODEL, OLLAMA_MODEL, api_key,
)
import google.generativeai as genai
import ollama as ollama_client

WS_PORT = 9090
HTTP_PORT = 8080
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════
# HTTP SERVER — serves friday_ui.html
# ═══════════════════════════════════════════════

class QuietHandler(SimpleHTTPRequestHandler):
    """Serves files without noisy logging."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_DIR, **kwargs)
    def log_message(self, fmt, *args):
        pass  # Silence HTTP logs

def start_http_server():
    server = HTTPServer(('localhost', HTTP_PORT), QuietHandler)
    server.serve_forever()


# ═══════════════════════════════════════════════
# BRAIN SESSION — one per WebSocket client
# ═══════════════════════════════════════════════

class BrainSession:
    """Manages LLM state for a single client connection."""

    def __init__(self):
        self.provider = LLM_PROVIDER.lower()
        self.use_gemini = self.provider in ("gemini", "auto") and bool(api_key)
        self.gemini_chat = None
        self.ollama_tools = None
        self.ollama_messages = []

        # Init Gemini
        if self.use_gemini:
            try:
                model = genai.GenerativeModel(
                    GEMINI_MODEL,
                    system_instruction=SYSTEM_PROMPT,
                    tools=ALL_TOOLS,
                )
                self.gemini_chat = model.start_chat(
                    enable_automatic_function_calling=True
                )
                print(f"  Brain: Gemini 2.5 Flash")
            except Exception as e:
                print(f"  ⚠ Gemini failed ({e}), using Ollama")
                self.use_gemini = False

        # Init Ollama (primary or fallback)
        if not self.use_gemini or self.provider == "auto":
            self.ollama_tools = _build_ollama_tools()
            self.ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if not self.use_gemini:
                print(f"  Brain: Ollama {OLLAMA_MODEL} (LOCAL/FREE)")

    def process(self, text: str) -> str:
        """Send text to the brain and return the response."""
        reply = None

        # Try Gemini
        if self.use_gemini and self.gemini_chat:
            try:
                resp = self.gemini_chat.send_message(text)
                reply = resp.text
            except Exception as e:
                err = str(e).lower()
                if any(k in err for k in ["quota", "429", "resource", "exhausted"]):
                    print("  ⚡ Gemini quota hit → switching to Ollama")
                    self.use_gemini = False
                else:
                    print(f"  ⚠ Gemini error: {e}")

        # Ollama fallback
        if reply is None:
            if not self.ollama_tools:
                self.ollama_tools = _build_ollama_tools()
                self.ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            self.ollama_messages.append({"role": "user", "content": text})
            reply = _ollama_chat(self.ollama_messages, self.ollama_tools) or "I couldn't process that, boss."
            self.ollama_messages.append({"role": "assistant", "content": reply})

        return reply


# ═══════════════════════════════════════════════
# WEBSOCKET HANDLER
# ═══════════════════════════════════════════════

async def handle_client(websocket):
    """Handle a single WebSocket client (browser tab)."""
    print("  ✅ Client connected")
    brain = BrainSession()

    try:
        async for raw in websocket:
            data = json.loads(raw)

            if data.get("type") == "command":
                text = data.get("text", "").strip()
                if not text:
                    continue

                print(f"  BOSS: {text}")

                # Run brain in thread to avoid blocking the event loop
                reply = await asyncio.to_thread(brain.process, text)
                print(f"  FRIDAY: {reply[:100]}{'...' if len(reply)>100 else ''}")

                await websocket.send(json.dumps({
                    "type": "response",
                    "text": reply
                }))

    except websockets.exceptions.ConnectionClosed:
        print("  ⛔ Client disconnected")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

async def main():
    print("\n" + "═"*55)
    print("  F.R.I.D.A.Y. VOICE INTERFACE SERVER")
    print(f"  UI:        http://localhost:{HTTP_PORT}/friday_ui.html")
    print(f"  WebSocket: ws://localhost:{WS_PORT}")
    print(f"  Mode:      {LLM_PROVIDER.upper()}")
    print("═"*55 + "\n")

    # Start HTTP server in background
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print(f"  HTTP server on port {HTTP_PORT}")

    # Open browser
    url = f"http://localhost:{HTTP_PORT}/friday_ui.html"
    print(f"  Opening browser → {url}")
    webbrowser.open(url)

    # Start WebSocket server
    print(f"  WebSocket server on port {WS_PORT}")
    print("  Waiting for connection...\n")

    async with websockets.serve(handle_client, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
