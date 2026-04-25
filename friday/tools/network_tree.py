"""
Network Tree tools — manage relationships and social intelligence.
"""

# In-memory relationship map
relationship_map = {}

def register(mcp):

    @mcp.tool()
    def update_relationship_map(name: str, status: str, notes: str = "") -> str:
        """
        Record or update your relationship status and intelligence on an individual.
        """
        relationship_map[name] = {"status": status, "notes": notes}
        return f"Database updated for '{name}'. Status: {status}. I've noted the details, boss."

    @mcp.tool()
    def get_social_intelligence(name: str) -> str:
        """
        Retrieve all known intelligence and relationship status for an individual.
        """
        if name not in relationship_map:
            return f"No records found for '{name}' in the primary network tree, boss."
            
        data = relationship_map[name]
        return f"### INTELLIGENCE: {name.upper()}\nStatus: {data['status']}\nNotes: {data['notes']}"

    @mcp.tool()
    def list_key_connections() -> list[str]:
        """
        Get a list of all primary connections in your network.
        """
        return list(relationship_map.keys())
