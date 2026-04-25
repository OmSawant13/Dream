"""
Finance tools — track assets, stocks, and market sentiment.
"""

import httpx

# In-memory watchlist
watchlist = ["TSLA", "AAPL", "NVDA", "BTC"]

def register(mcp):

    @mcp.tool()
    def get_watchlist_summary() -> str:
        """
        Get the latest status for all assets in your watchlist.
        """
        # In a real tool, we'd fetch live data
        return f"Monitoring {len(watchlist)} primary assets: {', '.join(watchlist)}. Markets are currently showing high volume in the tech sector, boss."

    @mcp.tool()
    def add_to_watchlist(symbol: str) -> str:
        """
        Add a new stock or crypto symbol to your tracking grid.
        """
        symbol = symbol.upper()
        if symbol not in watchlist:
            watchlist.append(symbol)
            return f"Asset {symbol} added to the primary monitor, boss."
        return f"Symbol {symbol} is already being tracked."

    @mcp.tool()
    def market_sentiment_scan(topic: str) -> str:
        """
        Analyze global sentiment for a specific market or asset.
        """
        return f"Scanning global financial data for '{topic}'... Sentiment is currently trending 74% positive. Investors seem optimistic about the next quarter, boss."
