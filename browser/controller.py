import logging
from playwright.async_api import async_playwright

logger = logging.getLogger("papper-controller")

class BrowserController:
    """Phase A: The CDP Link. Connects to an existing Chrome instance."""
    def __init__(self, cdp_url="http://127.0.0.1:9222"):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser = None
        self.context = None

    async def connect(self):
        """Establish the CDP bridge."""
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0]
            
            if not self.context.pages:
                await self.context.new_page()
            
            logger.info("✅ CDP Link Established.")
            return True
        except Exception as e:
            logger.error(f"❌ CDP Link Failed: {e}")
            return False

    async def get_active_page(self):
        if not self.context: await self.connect()
        # Returns the most active page
        page = self.context.pages[-1]
        return page

    async def disconnect(self):
        """Clean shutdown of playwright context."""
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
