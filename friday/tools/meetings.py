"""
Meeting tools — track action items and generate meeting summaries.
"""

from datetime import datetime

# In-memory storage for current meeting context
current_meeting = {
    "active": False,
    "start_time": None,
    "notes": [],
    "action_items": []
}

def register(mcp):

    @mcp.tool()
    def initialize_meeting_mode(topic: str) -> str:
        """
        Starts recording notes and action items for a formal briefing.
        """
        current_meeting["active"] = True
        current_meeting["start_time"] = datetime.now().isoformat()
        current_meeting["topic"] = topic
        current_meeting["notes"] = []
        current_meeting["action_items"] = []
        return f"Meeting mode initialized: '{topic}'. I'm recording all critical data now, boss."

    @mcp.tool()
    def log_meeting_note(note: str) -> str:
        """
        Add a specific note to the current meeting record.
        """
        if not current_meeting["active"]:
            return "No active meeting session, boss. Should I start one?"
        current_meeting["notes"].append(note)
        return "Note archived."

    @mcp.tool()
    def add_action_item(task: str, owner: str = "Boss") -> str:
        """
        Add a task to the current meeting's action item list.
        """
        if not current_meeting["active"]:
            return "No active meeting session."
        current_meeting["action_items"].append({"task": task, "owner": owner})
        return f"Action item added for {owner}: '{task}'."

    @mcp.tool()
    def finalize_meeting() -> str:
        """
        Ends the meeting and returns a full summary report.
        """
        if not current_meeting["active"]:
            return "No meeting in progress."
            
        summary = [f"### MEETING SUMMARY: {current_meeting.get('topic', 'General Briefing')}\n"]
        summary.append(f"Start Time: {current_meeting['start_time']}")
        summary.append("\n**NOTES:**")
        summary.extend([f"- {n}" for n in current_meeting["notes"]])
        summary.append("\n**ACTION ITEMS:**")
        summary.extend([f"- [{a['owner']}]: {a['task']}" for a in current_meeting["action_items"]])
        
        current_meeting["active"] = False
        return "\n".join(summary)
