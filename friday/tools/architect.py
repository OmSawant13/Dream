"""
Architect tools — write code, refactor files, and create new systems.
"""

import os

def register(mcp):

    @mcp.tool()
    def write_code_to_file(path: str, content: str) -> str:
        """
        Write or overwrite a file with new code content.
        Use this for 'Create a new script' or 'Fix this function'.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
            
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully deployed code to {path}, boss. Systems are ready."
        except Exception as e:
            return f"Architect failure: Unable to write to {path}. Error: {str(e)}"

    @mcp.tool()
    def create_new_tool(name: str, code: str) -> str:
        """
        Creates a new MCP tool module in the friday/tools directory.
        Meta-tool: FRIDAY can now expand her own capabilities.
        """
        path = f"friday/tools/{name}.py"
        try:
            with open(path, "w") as f:
                f.write(code)
            return f"New protocol '{name}' has been developed and integrated into my toolset, boss. Please restart the server to initialize it."
        except Exception as e:
            return f"Development error: Unable to create new protocol. {str(e)}"
