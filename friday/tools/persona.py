"""
Persona tools — switch between different AI assistant protocols (JARVIS, FRIDAY, etc.).
"""

def register(mcp):

    @mcp.tool()
    def switch_protocol(name: str) -> str:
        """
        Switch the assistant's personality and communication protocol.
        Available: 'FRIDAY', 'JARVIS', 'EDITH', 'JOCASTA'.
        """
        name = name.upper()
        if name not in ["FRIDAY", "JARVIS", "EDITH", "JOCASTA"]:
            return f"Protocol '{name}' is not recognized in the Stark core database, boss."
            
        return (
            f"### PROTOCOL SWITCH: {name}\n"
            f"Initializing {name} communication parameters. "
            f"Reconfiguring linguistic patterns and witty remark threshold... "
            f"Switch complete. Standing by as {name}, boss."
        )

    @mcp.tool()
    def get_available_protocols() -> list[str]:
        """
        Returns a list of all available AI personas.
        """
        return ["FRIDAY (Current)", "JARVIS (Witty, British)", "EDITH (Tactical)", "JOCASTA (Efficient)"]
