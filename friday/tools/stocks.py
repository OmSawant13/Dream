"""
STARK STOCK INTELLIGENCE
========================
Real-time market data using yfinance.
"""

import yfinance as yf

def get_stock_price(symbol: str) -> str:
    """Get the live price, change, and market cap for any ticker symbol."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        name = info.get('shortName') or symbol
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        change = info.get('regularMarketChangePercent', 0)
        mkt_cap = info.get('marketCap', 0)
        
        cap_str = f"${mkt_cap/1e12:.2f}T" if mkt_cap > 1e12 else f"${mkt_cap/1e9:.2f}B"
        
        return (f"{name} ({symbol.upper()})\n"
                f"Price: ${price:.2f}\n"
                f"Change: {change:+.2f}%\n"
                f"Market Cap: {cap_str}")
    except Exception as e:
        return f"Error fetching {symbol}: {e}"

def get_market_summary() -> str:
    """Brief overview of major indices (S&P 500, NASDAQ, Dow)."""
    indices = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "Dow Jones"}
    summary = []
    for sym, name in indices.items():
        try:
            t = yf.Ticker(sym)
            change = t.info.get('regularMarketChangePercent', 0)
            summary.append(f"{name}: {change:+.2f}%")
        except: continue
    return " | ".join(summary) if summary else "Markets currently unavailable."

def register(mcp):
    @mcp.tool()
    def get_stock_price_tool(symbol: str) -> str:
        """Get the live price, change, and market cap for any ticker symbol."""
        return get_stock_price(symbol)

    @mcp.tool()
    def get_market_summary_tool() -> str:
        """Brief overview of major indices (S&P 500, NASDAQ, Dow)."""
        return get_market_summary()
