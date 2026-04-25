"""
Wellness protocols — track health, posture, and hydration.
"""

from datetime import datetime

# In-memory storage for health data
health_data = {
    "hydration": 0,
    "breaks_taken": 0,
    "last_posture_check": None
}

def log_hydration(amount_ml: int) -> str:
    """
    Record water intake in milliliters.
    """
    health_data["hydration"] += amount_ml
    return f"Intake recorded, boss. Total hydration for today: {health_data['hydration']}ml. Stay sharp."

def check_wellness_status() -> dict:
    """
    Get a summary of your health and wellness stats for the day.
    """
    return {
        "hydration": f"{health_data['hydration']}ml",
        "posture_status": "Monitoring active",
        "suggestion": "Time for a 5-minute break and some eye exercises, boss."
    }

def log_posture_check() -> str:
    """
    Mark that the boss has corrected their posture.
    """
    health_data["last_posture_check"] = datetime.now().isoformat()
    return "Posture correction noted. Spinal alignment optimized."

def register(mcp):
    @mcp.tool()
    def log_hydration_tool(amount_ml: int) -> str:
        return log_hydration(amount_ml)

    @mcp.tool()
    def check_wellness_status_tool() -> dict:
        return check_wellness_status()

    @mcp.tool()
    def log_posture_check_tool() -> str:
        return log_posture_check()

