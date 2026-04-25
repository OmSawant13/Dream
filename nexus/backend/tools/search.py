import httpx

def web_search(query: str) -> str:
    """Searches the internet for information. Use this if you don't know the answer."""
    try:
        # Simple search using a public API or scraper
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        resp = httpx.get(url, timeout=10)
        data = resp.json()
        
        abstract = data.get("AbstractText", "")
        if abstract:
            return f"Search Result: {abstract}"
        
        # Fallback to direct results
        related = data.get("RelatedTopics", [])
        if related:
            return f"Search Result: {related[0].get('Text', 'No specific info found.')}"
            
        return "I scanned the grid, but couldn't find a definitive answer. I'll keep looking."
    except Exception as e:
        return f"Search Error: {e}"
