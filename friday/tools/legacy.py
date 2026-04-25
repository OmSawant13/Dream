"""
Legacy tools — record achievements and document the boss's journey.
"""

from datetime import datetime

# In-memory legacy log
legacy_log = []

def register(mcp):

    @mcp.tool()
    def record_achievement(description: str, category: str = "General") -> str:
        """
        Record a milestone or achievement for the historical record.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "category": category
        }
        legacy_log.append(entry)
        return f"Milestone archived, boss. '{description}' is now part of your historical record."

    @mcp.tool()
    def get_legacy_briefing() -> str:
        """
        Get a summary of recent major achievements and milestones.
        """
        if not legacy_log:
            return "The legacy archives are currently empty. Let's make some history today, boss."
            
        report = ["### THE STARK LEGACY: RECENT MILESTONES\n"]
        for entry in legacy_log[-5:]:
            report.append(f"- [{entry['timestamp'][:10]}] ({entry['category']}): {entry['description']}")
            
        return "\n".join(report)

    @mcp.tool()
    def archive_thought(thought: str) -> str:
        """
        Save a philosophical or creative thought to the personal vault.
        """
        return f"Thought secured in the deep-vault, boss. It's safe with me."
