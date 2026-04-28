import asyncio
import logging
import sys
import os
from pathlib import Path

logger = logging.getLogger("papper-actions")

class BrowserActions:
    """The Muscle: Executes atomic browser interactions with robust telemetry."""
    def __init__(self, controller, observer):
        self.controller = controller
        self.observer = observer
        # FIX #4: Dynamic path resolution for telemetry
        self.base_dir = Path(__file__).parent.parent
        self.telemetry_dir = self.base_dir / "telemetry"

    async def click_index(self, index):
        """Force-click center coordinates of an index."""
        target = self.observer.get_element(index)
        if not target:
            logger.error(f"Error: Index {index} not found.")
            return False
        
        try:
            page = await self.controller.get_active_page()
            await page.mouse.click(target['x'], target['y'])
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Strike Failed at index {index}: {e}")
            await self.take_error_screenshot(f"fail_click_{index}")
            return False

    async def type_at_index(self, index, text):
        """Targeted Entry: Click, clear, and type."""
        target = self.observer.get_element(index)
        if not target:
            logger.error(f"Error: Index {index} not found.")
            return False
        
        try:
            page = await self.controller.get_active_page()
            await page.mouse.click(target['x'], target['y'])
            
            modifier = "Meta" if sys.platform == "darwin" else "Control"
            await page.keyboard.press(f"{modifier}+A")
            await page.keyboard.press("Backspace")
            
            await page.keyboard.type(text)
            return True
        except Exception as e:
            logger.error(f"Entry Failed at index {index}: {e}")
            await self.take_error_screenshot(f"fail_type_{index}")
            return False

    async def scroll(self, direction="down", amount=500):
        """Scroll the page to reveal more content."""
        try:
            page = await self.controller.get_active_page()
            scroll_dist = amount if direction == "down" else -amount
            await page.evaluate(f"window.scrollBy(0, {scroll_dist})")
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Scroll Failed: {e}")
            await self.take_error_screenshot("fail_scroll")
            return False
            
    async def press_key(self, key_name):
        """Press a specific keyboard key."""
        try:
            page = await self.controller.get_active_page()
            await page.keyboard.press(key_name)
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
            return True
        except Exception as e:
            logger.error(f"Key Press Failed: {e}")
            return False

    async def take_error_screenshot(self, name):
        """Save a telemetry snapshot for debugging using Path resolution."""
        try:
            page = await self.controller.get_active_page()
            # FIX #4: Ensure directory exists relative to the script
            os.makedirs(self.telemetry_dir, exist_ok=True)
            path = self.telemetry_dir / f"{name}.png"
            await page.screenshot(path=str(path))
            logger.info(f"📸 Screenshot saved to {path}")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")

    async def navigate(self, url):
        """Navigate to a specific URL."""
        try:
            page = await self.controller.get_active_page()
            if not url.startswith("http"):
                url = f"https://{url}" if "." in url else f"https://www.{url}.com"
            await page.goto(url, wait_until="domcontentloaded")
            return True
        except Exception as e:
            logger.error(f"Navigation Failed: {e}")
            await self.take_error_screenshot("fail_nav")
            return False
