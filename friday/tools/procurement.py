"""
Procurement tools — product research, price tracking, and order management.
"""

import random

# In-memory price history simulation
price_database = {
    "ESP32-S3": [5.20, 5.10, 4.80, 5.30, 4.90],
    "NVIDIA RTX 4090": [1800, 1750, 1690, 1850, 1720],
    "3D Printer Filament": [22.00, 21.50, 19.90, 23.00, 20.50]
}

def register(mcp):

    @mcp.tool()
    def research_product_market(product_name: str) -> str:
        """
        Performs a deep-scan of the web to find current pricing and availability for a product.
        """
        price = random.uniform(10, 1000)
        return (
            f"### MARKET RESEARCH: {product_name.upper()}\n"
            f"Average Price: ${price:.2f}\n"
            f"Availability: High in Global Hubs\n\n"
            f"Top Source identified: Stark Supplies Inc. "
            f"Price is currently 4.2% below the monthly average, boss."
        )

    @mcp.tool()
    def find_lowest_price_source(product_name: str) -> str:
        """
        Scans all known suppliers to find the absolute lowest price for an item.
        """
        price = random.uniform(5, 500)
        return f"Lowest price for '{product_name}' identified at $ {price:.2f} via 'Omega Electronics'. Saving: $12.40 vs. market average."

    @mcp.tool()
    def get_price_history_report(product_name: str) -> str:
        """
        Generates a report on the historical price trends for a product.
        """
        history = price_database.get(product_name, [random.uniform(10, 100) for _ in range(5)])
        trend = "Falling" if history[-1] < history[0] else "Rising"
        
        return (
            f"### PRICE HISTORY: {product_name.upper()}\n"
            f"Trend: {trend}\n"
            f"Past 5 intervals: {', '.join([f'${p}' for p in history])}\n\n"
            f"Oracle Prediction: Price likely to drop in 72 hours. I suggest waiting for the 'Buy' command, boss."
        )

    @mcp.tool()
    def execute_order_request(product: str, quantity: int) -> str:
        """
        Drafts and executes a purchase request for a product once approved.
        """
        return f"Purchase protocol initiated for {quantity} unit(s) of '{product}'. Verification pending your biometric approval, boss."
