"""
Memory tools — persistent storage for facts and emotional state tracking.
"""

import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"

def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"facts": {}, "mood": "neutral", "last_updated": None}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"facts": {}, "mood": "neutral", "last_updated": None}

def _save_memory(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def register(mcp):

    @mcp.tool()
    def store_fact(fact: str) -> str:
        """
        Store a new fact about the boss or their preferences.
        Use this when the user tells you something they want you to remember.
        Example: 'My favorite coffee is Espresso' -> store_fact('favorite coffee: Espresso')
        """
        data = _load_memory()
        # Generate a simple key or just append to a list
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["facts"][timestamp] = fact
        _save_memory(data)
        return f"Understood, boss. I've committed that to memory: '{fact}'"

    @mcp.tool()
    def recall_facts(query: str = "") -> str:
        """
        Recall facts about the boss. If query is provided, it filters for relevant facts.
        Use this when you need to remember something the user told you previously.
        """
        data = _load_memory()
        facts = data.get("facts", {})
        
        if not facts:
            return "My memory banks are currently empty regarding those details, boss."
            
        if not query:
            formatted_facts = "\n".join([f"- [{k}]: {v}" for k, v in facts.items()])
            return f"Here is everything I remember, boss:\n{formatted_facts}"
            
        # Simple keyword filtering
        relevant = [v for v in facts.values() if query.lower() in v.lower()]
        if not relevant:
            return f"I don't seem to have any records matching '{query}', boss."
            
        return f"Regarding '{query}', here is what I know: " + ", ".join(relevant)

    @mcp.tool()
    def update_mood(mood: str) -> str:
        """
        Update the detected mood of the boss.
        Use this to track how the user is feeling based on their tone or words.
        """
        data = _load_memory()
        old_mood = data.get("mood", "neutral")
        data["mood"] = mood
        _save_memory(data)
        
        if mood.lower() in ["angry", "stressed", "frustrated"]:
            return f"Detected tension. Adjusting my protocols to be more supportive. Mood updated from {old_mood} to {mood}."
        return f"Acknowledged. Mood updated to {mood}."

    @mcp.tool()
    def get_status_report() -> dict:
        """
        Get a summary of FRIDAY's current status, including remembered facts and the boss's mood.
        """
        data = _load_memory()
        return {
            "mood": data.get("mood", "neutral"),
            "known_facts_count": len(data.get("facts", {})),
            "last_memory_update": data.get("last_updated"),
            "system_status": "All systems operational. Standing by."
        }
