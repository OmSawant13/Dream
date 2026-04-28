import asyncio
import logging
from pathlib import Path
from browser.controller import BrowserController
from browser.observer import BrowserObserver
from browser.actions import BrowserActions

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

async def manual_loop():
    print("\n" + "═"*55)
    print(" PAPPER TERMINAL: LEVEL 1 PRO (ELITE) ")
    print("═"*55)
    print("COMMANDS: goto [url], click [idx], type [idx] [txt], scroll [up/down], key [name], exit")
    
    controller = BrowserController()
    observer = BrowserObserver(controller)
    actions = BrowserActions(controller, observer)
    
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
                
                if action in ["goto", "click", "type", "scroll", "key"] and len(parts) < 2:
                    print(f"❌ Error: '{action}' command needs an argument.")
                    continue

                if action == "goto":
                    success = await actions.navigate(parts[1])
                    if not success: print("❌ Navigation Failed. See papper_terminal/telemetry/")
                elif action == "click":
                    success = await actions.click_index(parts[1])
                    if not success: print("❌ Strike Failed. See papper_terminal/telemetry/")
                elif action == "type":
                    idx_part = parts[1].split(" ", 1)
                    if len(idx_part) < 2:
                        print("❌ Error: 'type' needs [index] [text]")
                        continue
                    success = await actions.type_at_index(idx_part[0], idx_part[1].strip("'\""))
                    if not success: print("❌ Type Failed. See papper_terminal/telemetry/")
                elif action == "scroll":
                    direction = parts[1] if parts[1] in ["up", "down"] else "down"
                    success = await actions.scroll(direction)
                    if not success: print("❌ Scroll Failed.")
                elif action == "key":
                    success = await actions.press_key(parts[1])
                    if not success: print("❌ Key Press Failed.")
                else:
                    print(f"Unknown command: {action}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Action Execution Error: {e}")
                print(f"⚠️ Action Error: {e}")

    finally:
        # Clean shutdown on exit
        await controller.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(manual_loop())
    except KeyboardInterrupt:
        print("\nExiting Papper Terminal.")
