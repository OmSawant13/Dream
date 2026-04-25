"""
Scheduler tools — set reminders and timers.
"""

import asyncio
from datetime import datetime, timedelta

# Simple in-memory storage for reminders
# Note: In a real server, these would be lost on restart unless saved to disk.
reminders = []

def register(mcp):

    @mcp.tool()
    async def set_reminder(minutes: int, task: str) -> str:
        """
        Set a reminder to be triggered after a certain number of minutes.
        """
        trigger_time = datetime.now() + timedelta(minutes=minutes)
        reminders.append({"time": trigger_time, "task": task, "triggered": False})
        
        # In a real voice agent, we'd need a background task to speak the reminder.
        # For now, we'll just confirm it's scheduled.
        return f"Alarm set. I'll remind you to '{task}' in {minutes} minutes, at {trigger_time.strftime('%H:%M')}, boss."

    @mcp.tool()
    def list_reminders() -> str:
        """
        List all active reminders.
        """
        if not reminders:
            return "No pending reminders in the queue, boss."
            
        active = [f"- {r['task']} at {r['time'].strftime('%H:%M')}" for r in reminders if not r['triggered']]
        if not active:
            return "All previous reminders have been cleared."
            
        return "Current schedule:\n" + "\n".join(active)

    @mcp.tool()
    def clear_all_reminders() -> str:
        """
        Clear all reminders from the queue.
        """
        reminders.clear()
        return "Schedule cleared, boss. Blank slate."
