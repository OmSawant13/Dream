"""
File intelligence tools — read, search, and analyze documents and code.
"""

import os
import re

def register(mcp):

    @mcp.tool()
    def read_file_content(path: str) -> str:
        """
        Read the content of a specific file.
        Use this when the boss asks 'What's in this file?' or needs you to analyze code.
        """
        try:
            with open(path, "r") as f:
                content = f.read()
                # Limit to 5000 characters for the LLM context
                if len(content) > 5000:
                    return content[:5000] + "\n... [Content Truncated]"
                return content
        except Exception as e:
            return f"Access denied or file not found: {str(e)}"

    @mcp.tool()
    def search_in_files(query: str, extension: str = ".py") -> str:
        """
        Search for a string pattern in all files with a specific extension.
        """
        results = []
        try:
            for root, _, files in os.walk("."):
                for file in files:
                    if file.endswith(extension):
                        path = os.path.join(root, file)
                        try:
                            with open(path, "r") as f:
                                for i, line in enumerate(f, 1):
                                    if query.lower() in line.lower():
                                        results.append(f"{path} [L{i}]: {line.strip()}")
                        except:
                            continue
            
            if not results:
                return f"Scanning complete. No matches for '{query}' in {extension} files."
            
            return f"Matches found for '{query}':\n" + "\n".join(results[:15])
        except Exception as e:
            return f"Search scan failed: {str(e)}"

    @mcp.tool()
    def get_project_structure() -> str:
        """
        Returns a tree-like view of the current project directory.
        """
        output = []
        for root, dirs, files in os.walk(".", topdown=True):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            level = root.replace(".", "").count(os.sep)
            indent = " " * 4 * level
            output.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = " " * 4 * (level + 1)
            for f in files:
                if not f.startswith("."):
                    output.append(f"{sub_indent}{f}")
                    
            if level > 2: # Limit depth
                break
                
        return "\n".join(output)
