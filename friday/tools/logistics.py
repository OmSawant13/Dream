"""
Logistics tools — manage inventory, procurement, and shipping.
"""

# In-memory inventory
inventory = {
    "ESP32 Boards": 5,
    "Solder Wire (m)": 15,
    "LEDs (RGB)": 50,
    "Jumper Wires": 100
}

def register(mcp):

    @mcp.tool()
    def check_inventory(item: str = "") -> str:
        """
        Check the current stock levels of Stark Industries hardware.
        """
        if not item:
            levels = "\n".join([f"- {k}: {v}" for k, v in inventory.items()])
            return f"Current inventory status:\n{levels}\n\nStatus: Supplies are sufficient for current projects."
            
        # Search for item
        matches = {k: v for k, v in inventory.items() if item.lower() in k.lower()}
        if not matches:
            return f"No records of '{item}' in the current logistics grid, boss."
            
        return "\n".join([f"- {k}: {v}" for k, v in matches.items()])

    @mcp.tool()
    def add_to_procurement_list(item: str, quantity: int = 1) -> str:
        """
        Adds an item to the list of supplies to be ordered.
        """
        return f"Acknowledged. Added {quantity} unit(s) of '{item}' to the procurement queue. I'll handle the ordering protocols, boss."

    @mcp.tool()
    def track_logistics_shipment(tracking_id: str) -> str:
        """
        Simulates tracking a shipment from Stark Industries suppliers.
        """
        return f"Tracking ID {tracking_id} identified. Current status: In transit via Stark Jet 4. Estimated arrival: 14:00 hours."
