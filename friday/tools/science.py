"""
Scientific intelligence tools — search and summarize academic papers from arXiv.
"""

import httpx
import xml.etree.ElementTree as ET

def register(mcp):

    @mcp.tool()
    async def search_arxiv(query: str, max_results: int = 5) -> str:
        """
        Search for scientific papers on arXiv.
        Use this for 'Research new technologies' or 'Deep technical briefings'.
        """
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entries = root.findall('atom:entry', namespace)
                if not entries:
                    return f"I've scanned the scientific archives, boss. No records found for '{query}'."
                
                briefing = [f"### SCIENTIFIC BRIEFING: {query.upper()}\n"]
                for entry in entries:
                    title = entry.find('atom:title', namespace).text.strip()
                    summary = entry.find('atom:summary', namespace).text.strip()
                    briefing.append(f"**Title:** {title}")
                    briefing.append(f"**Abstract:** {summary[:300]}...\n")
                
                return "\n".join(briefing)
            except Exception as e:
                return f"Unable to access the scientific grid: {str(e)}"

    @mcp.tool()
    def cite_source(title: str, link: str) -> str:
        """
        Formally cite a source in Stark Industries format.
        """
        return f"Source archived: '{title}' - URI: {link}. Intelligence verified."
