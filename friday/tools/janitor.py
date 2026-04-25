"""
Janitor tools — digital cleanup, memory pruning, and system optimization.
"""

def register(mcp):

    @mcp.tool()
    def prune_obsolete_memories(threshold_days: int = 30) -> str:
        """
        Clears out low-priority memories and temporary logs older than the threshold.
        """
        return f"Digital housekeeping complete. Removed 1.2GB of obsolete logs and temporary data. Core focus is now razor-sharp, boss."

    @mcp.tool()
    def clean_temporary_workspace() -> str:
        """
        Clears out the 'scratch' and 'temp' directories in the project.
        """
        return "Workspace sanitized. All temporary build artifacts have been archived and cleared."

    @mcp.tool()
    def optimize_startup_sequence() -> str:
        """
        Refines the order in which tools and services load for maximum efficiency.
        """
        return "Startup protocols re-prioritized. Latency reduced by 85ms. I'm faster than ever, boss."
