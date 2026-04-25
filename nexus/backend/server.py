import json
import asyncio
import threading
import speech_recognition as sr
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from brain import FridayBrain
from tool_manager import ToolManager

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

tool_mgr = ToolManager()
brain = FridayBrain(provider="ollama", tools=tool_mgr.get_all_tools())

DIRECT_COMMANDS = {
    "open youtube": ("play_entertainment", {"platform": "youtube"}),
    "open spotify": ("play_entertainment", {"platform": "spotify"}),
    "open whatsapp": ("whatsapp_command", {"contact": "om7"}),
}

async def process_command(cmd, websocket):
    cmd = cmd.lower().strip()
    print(f"📡 Processing: {cmd}")
    
    # 1. Direct-Link Check
    for trigger, (tool_name, args) in DIRECT_COMMANDS.items():
        if trigger in cmd:
            tool_func = brain.tools_map.get(tool_name)
            if tool_func:
                # Run in background
                asyncio.create_task(asyncio.to_thread(tool_func, **args))
                await websocket.send_text(json.dumps({"type": "chunk", "text": "Protocol Engaged. Opening now. "}))
                # CRITICAL: Send done signal to reset UI
                await websocket.send_text(json.dumps({"type": "done", "text": "Action complete, Boss."}))
                return

    # 2. Brain Processing
    try:
        full_text = ""
        for chunk in brain.chat_stream(cmd):
            full_text += chunk
            await websocket.send_text(json.dumps({"type": "chunk", "text": chunk}))
        await websocket.send_text(json.dumps({"type": "done", "text": full_text}))
    except Exception as e:
        print(f"⚠️ Brain Error: {e}")
        await websocket.send_text(json.dumps({"type": "done", "text": "Neural link unstable. Direct commands only."}))

def listen_loop(loop, websocket):
    recognizer = sr.Recognizer()
    try:
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio)
                    asyncio.run_coroutine_threadsafe(process_command(text, websocket), loop)
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_text(json.dumps({"type": "transcript", "text": text})), loop
                    )
                except: pass
    except: pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()
    threading.Thread(target=listen_loop, args=(loop, websocket), daemon=True).start()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            if payload["type"] == "command":
                await process_command(payload["text"], websocket)
    except: pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
