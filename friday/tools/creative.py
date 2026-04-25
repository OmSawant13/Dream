"""
Creative tools — generate visual concepts and R&D descriptions.
"""

def register(mcp):

    @mcp.tool()
    def generate_visual_concept(description: str) -> str:
        """
        Generates a detailed visual R&D concept based on a description.
        Use this when the boss asks for 'Visuals', 'Concepts', or 'Designs'.
        """
        # This tool provides the structured prompt for a vision model or image generator.
        return (
            f"### CONCEPTUAL DESIGN ARCHIVE\n\n"
            f"**Project:** Stark R&D Concept\n"
            f"**Subject:** {description}\n\n"
            f"Generating high-fidelity schematics and visual renders now, boss. "
            f"Stand by for the visual feed."
        )

    @mcp.tool()
    def refine_design(current_design: str, changes: str) -> str:
        """
        Refine an existing design with specific changes.
        """
        return f"Applying structural refinements to {current_design}: {changes}. Recalculating tolerances."
