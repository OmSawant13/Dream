"""
Papper MCP Server — Entry Point
Run with: python server.py
"""

from mcp.server.fastmcp import FastMCP
from papper.tools import register_all_tools
from papper.prompts import register_all_prompts
from papper.resources import register_all_resources
from papper.config import config

# Create the MCP server instance
mcp = FastMCP(
    name=config.SERVER_NAME,
    instructions=(
        "You are Papper, a Tony Stark-style AI assistant. "
        "You have access to a set of tools to help the user. "
        "Be concise, accurate, and a little witty."
    ),
)

# Register tools, prompts, and resources
register_all_tools(mcp)
register_all_prompts(mcp)
register_all_resources(mcp)

def main():
    mcp.run(transport='sse')

if __name__ == "__main__":
    main()