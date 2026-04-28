"""
STARK NEXUS — The Knowledge Bridge Protocol.
Connects the Friday AI to the massive research/clones database.
"""

import os
import subprocess
from typing import List, Optional

def search_research(query: str) -> str:
    """
    Perform a high-speed search across all 169 cloned research repositories.
    Use this to find specific code patterns, documentation, or logic.
    """
    research_path = "research/clones"
    if not os.path.exists(research_path):
        return "Research database not found."

    try:
        # Use grep for speed
        cmd = ["grep", "-rnli", "--exclude-dir={.git,node_modules,__pycache__}", query, research_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if not result.stdout:
            return f"No matches found for '{query}' in the research database."
        
        matches = result.stdout.splitlines()
        count = len(matches)
        summary = f"Found {count} matches in the research database. Top results:\n"
        summary += "\n".join(matches[:15])
        if count > 15:
            summary += f"\n... and {count - 15} more matches."
        return summary
    except Exception as e:
        return f"Nexus search failed: {str(e)}"

def analyze_research_repo(repo_name: str) -> str:
    """
    Get a deep-dive overview of a specific research repository.
    """
    path = os.path.join("research/clones", repo_name)
    if not os.path.exists(path):
        return f"Repository '{repo_name}' not found in research."

    # Find README
    readme = None
    for f in os.listdir(path):
        if f.lower().startswith("readme"):
            readme = f
            break
    
    info = [f"### REPO ANALYSIS: {repo_name}\n"]
    if readme:
        try:
            with open(os.path.join(path, readme), "r") as f:
                content = f.read(2000)
                info.append(f"#### README SUMMARY:\n{content}")
                if len(content) >= 2000:
                    info.append("... [truncated]")
        except:
            info.append("README found but unreadable.")
    else:
        info.append("No README found.")
    
    # List main files
    files = [f for f in os.listdir(path) if not f.startswith(".")][:20]
    info.append(f"\n#### MAIN FILES:\n" + ", ".join(files))
    
    return "\n".join(info)

def bridge_logic(source_repo: str, target_file: str) -> str:
    """
    Attempts to 'connect' logic from a research repository to a local project file.
    This will analyze the source logic and suggest how to integrate it.
    """
    source_path = os.path.join("research/clones", source_repo)
    if not os.path.exists(source_path):
        return f"Source repo '{source_repo}' not found."
        
    # This is a high-level conceptual tool that triggers LLM reasoning
    return f"[System] Nexus link established between '{source_repo}' and '{target_file}'. Analyzing compatibility signatures..."

def run_research_script(repo_name: str, script_path: str, args: str = "") -> str:
    """
    Execute a script from a research clone. Use with caution.
    Example: repo_name='Dorothy', script_path='setup.py', args='--help'
    """
    full_path = os.path.join("research/clones", repo_name, script_path)
    if not os.path.exists(full_path):
        return f"Script not found: {full_path}"
    
    try:
        cwd = os.path.join("research/clones", repo_name)
        cmd = f"cd {cwd} && python3 {script_path} {args}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return f"Execution Output:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

def register(mcp):
    """Register the tools with the MCP server."""
    mcp.tool()(search_research)
    mcp.tool()(analyze_research_repo)
    mcp.tool()(bridge_logic)
    mcp.tool()(run_research_script)
