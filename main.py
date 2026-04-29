import asyncio
import logging
import sys
from pathlib import Path
from browser.controller import BrowserController
from browser.observer import BrowserObserver
from browser.actions import BrowserActions
from agent.agent import PapperAgent

# FIX: Robust path resolution for logging
BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "papper.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("papper-main")

async def ai_loop(task):
    """Trigger the autonomous Level 2 loop."""
    controller = BrowserController()
    if not await controller.connect():
        print("\n[ERROR]: Ensure Chrome is running on port 9222.")
        return

    agent = PapperAgent(controller)
    try:
        await agent.run(task)
    finally:
        await controller.disconnect()

async def manual_loop():
    print("\n" + "═"*55)
    print(" PAPPER TERMINAL: LEVEL 2 HYBRID ")
    print("═"*55)
    print("COMMANDS: ai [task], goto [url], click [idx], type [idx] [txt], scroll [up/down], key [name], exit")

    controller = BrowserController()
    observer = BrowserObserver(controller)
    actions = BrowserActions(controller, observer)
    agent = PapperAgent(controller)

    if not await controller.connect():
        print("\n[ERROR]: Ensure Chrome is running on port 9222.")
        return

    try:
        while True:
            print("\nScanning page state (Shadow DOM & Sorting V2)...")
            view = await observer.capture_grid()
            print(view)

            raw_input = input("\nPAPPER> ").strip()
            if not raw_input or raw_input.lower() in ["exit", "quit"]: break

            try:
                parts = raw_input.split(" ", 1)
                action = parts[0].lower()

                if action == "ai":
                    if len(parts) < 2:
                        print("❌ Error: 'ai' command needs a task description.")
                        continue
                    # FIX #5: Reuse same controller + agent instead of disconnect/reconnect
                    task = parts[1]
                    logger.info(f"🧠 Switching to autonomous mode for task: {task}")
                    result = await agent.run(task)
                    logger.info(f"🎯 Autonomous task {'completed' if result else 'failed'}.")
                    continue

                if action in ["goto", "click", "type", "scroll", "key"] and len(parts) < 2:
                    print(f"❌ Error: '{action}' command needs an argument.")
                    continue

                result = {"status": "error", "message": "Unknown command"}
                
                if action == "goto":
                    result = await actions.navigate(parts[1])
                elif action == "click":
                    result = await actions.click_index(parts[1])
                elif action == "type":
                    idx_part = parts[1].split(" ", 1)
                    if len(idx_part) < 2:
                        print("❌ Error: 'type' needs [index] [text]")
                        continue
                    result = await actions.type_at_index(idx_part[0], idx_part[1].strip("'\""))
                elif action == "scroll":
                    direction = parts[1] if parts[1] in ["up", "down"] else "down"
                    result = await actions.scroll(direction)
                elif action == "key":
                    result = await actions.press_key(parts[1])
                
                if result["status"] == "error":
                    print(f"❌ {result['message']}")
                else:
                    print(f"✅ {result['message']}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Action Execution Error: {e}")
                print(f"⚠️ Action Error: {e}")

    finally:
        await controller.disconnect()

if __name__ == "__main__":
    try:
        # Check for direct AI command from CLI
        if len(sys.argv) > 2 and sys.argv[1] == "ai":
            asyncio.run(ai_loop(" ".join(sys.argv[2:])))
        else:
            asyncio.run(manual_loop())
    except KeyboardInterrupt:
        print("\nExiting Papper Terminal.")
