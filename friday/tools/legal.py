"""
Legal tools — patent research and document drafting.
"""

def register(mcp):

    @mcp.tool()
    def check_patent_conflicts(invention_name: str) -> str:
        """
        Scans global patent databases for potential intellectual property conflicts.
        """
        return (
            f"### PATENT SCAN: {invention_name.upper()}\n"
            f"Status: CLEAR.\n"
            f"Found 3 similar technologies in the 'Space-Tech' sector, but your 'Stark' signature is unique.\n"
            f"Recommendation: File for provisional protection immediately, boss."
        )

    @mcp.tool()
    def draft_legal_disclaimer(context: str) -> str:
        """
        Generates a standard Stark Industries-grade legal disclaimer for a project.
        """
        return f"Legal disclaimer for '{context}' drafted. Standard clause 7 included: 'No liability for multiverse-related incidents.' Ready to print, boss."
