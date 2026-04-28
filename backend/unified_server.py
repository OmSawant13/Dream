import os
import json
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import uvicorn

from friday.core.brain import FridayBrain
from friday.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UnifiedServer")

app = FastAPI(title="F.R.I.D.A.Y. Unified Core")
brain = FridayBrain()

class CommandRequest(BaseModel):
    command: str
    client_id: str = "nexus_hud"

@app.get("/")
async def root():
    return {"status": "ONLINE", "version": "2.0-UNIFIED"}

@app.post("/command")
async def handle_command_rest(req: CommandRequest):
    """REST endpoint for the Desktop HUD."""
    try:
        result = await brain.process_command(req.command)
        return result
    except Exception as e:
        logger.error(f"Error handling REST command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the Web UI."""
    await websocket.accept()
    logger.info("WebSocket client connected.")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "command":
                command_text = message.get("text", "")
                logger.info(f"Received WS command: {command_text}")
                
                # Process through brain
                result = await brain.process_command(command_text)
                
                # Send back in the format expected by friday_ui.html
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "text": result.get("response", "")
                }))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

@app.get("/history")
async def get_history():
    """Returns the recent conversation history."""
    return brain.history

@app.get("/tools")
async def get_tools():
    """Returns the list of available tools and their metadata."""
    from friday.core.tool_manager import tool_manager
    return tool_manager.get_tool_metadata()

if __name__ == "__main__":
    logger.info("Igniting F.R.I.D.A.Y. Unified Core...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
