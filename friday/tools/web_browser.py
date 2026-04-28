"""
ADVANCED BROWSER PROTOCOL (via browser-use)
===========================================
Allows F.R.I.D.A.Y. to control a web browser like a human.
"""

import asyncio
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from friday.config import config

def register(mcp):

    @mcp.tool()
    async def perform_browser_task(task_description: str) -> str:
        """
        Performs a complex task in the web browser (e.g. 'find a flight to NYC', 'order pizza', 'search for a paper').
        This tool uses advanced AI to navigate websites, click buttons, and extract information.
        """
        if not config.GOOGLE_API_KEY:
            return "Boss, I need a Google API Key to initiate the browser-use protocol."

        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=config.GOOGLE_API_KEY)
            agent = Agent(
                task=task_description,
                llm=llm,
            )
            result = await agent.run()
            return f"Browser Task Complete: {result}"
        except Exception as e:
            return f"Browser Uplink Failure: {str(e)}"

    @mcp.tool()
    async def capture_web_data(url: str, query: str) -> str:
        """
        Goes to a specific URL and extracts information based on a query.
        """
        return await perform_browser_task(f"Go to {url} and find: {query}")
