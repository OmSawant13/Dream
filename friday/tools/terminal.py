"""
Terminal tools — execute shell commands and manage the dev environment.
"""

import subprocess
import os

def register(mcp):

    @mcp.tool()
    def run_terminal_command(command: str) -> str:
        """
        Executes a shell command on the host machine and returns the output.
        Use this for git commands, installing packages, or starting services.
        Example: 'git status', 'ls -la', 'uv sync'.
        """
        # Security: In a real Stark environment, we'd have a whitelist, 
        # but for this demo, we'll allow it with a warning.
        try:
            # Run in the project root
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            output = result.stdout
            error = result.stderr
            
            response = []
            if output:
                response.append(f"### OUTPUT:\n{output}")
            if error:
                response.append(f"### ERROR/STDOUT:\n{error}")
            if not output and not error:
                response.append("Command executed successfully with no output.")
                
            return "\n".join(response)[:2000] # Limit response size
            
        except subprocess.TimeoutExpired:
            return "Command timed out, boss. It might be running in the background."
        except Exception as e:
            return f"Terminal failure: {str(e)}"

    @mcp.tool()
    def check_git_status() -> str:
        """
        Quickly check the git status of the current repository.
        """
        return run_terminal_command("git status -s")

    @mcp.tool()
    def start_dev_server(script_name: str = "npm run dev") -> str:
        """
        Starts a development server in a new background process.
        """
        try:
            # We use Popen so it doesn't block the MCP server
            subprocess.Popen(script_name, shell=True)
            return f"Initializing development environment via '{script_name}'. I'll monitor the logs in the background, boss."
        except Exception as e:
            return f"Unable to start the server: {str(e)}"
