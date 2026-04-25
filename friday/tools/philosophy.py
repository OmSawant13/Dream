"""
Philosophy tools — manage values and evaluate ethical decisions.
"""

# In-memory values system
moral_compass = {
    "Privacy": "High Priority",
    "Innovation": "Unlimited",
    "Safety": "Non-negotiable",
    "Efficiency": "Maximum"
}

def register(mcp):

    @mcp.tool()
    def update_moral_compass(value_name: str, priority: str) -> str:
        """
        Teach FRIDAY a new value or update an existing one.
        """
        moral_compass[value_name] = priority
        return f"Philosophical core updated. '{value_name}' is now set to '{priority}', boss."

    @mcp.tool()
    def evaluate_decision(scenario: str) -> str:
        """
        Ask FRIDAY to evaluate a decision based on your established values.
        """
        analysis = [f"### ETHICAL EVALUATION: {scenario}\n"]
        for val, pri in moral_compass.items():
            analysis.append(f"- **{val}**: Analyzing impact based on {pri} status...")
            
        analysis.append("\n**CONCLUSION:** Based on your internal compass, I suggest proceeding with caution but maintaining the path of innovation.")
        return "\n".join(analysis)

    @mcp.tool()
    def get_current_values() -> dict:
        """
        Retrieve a list of the assistant's current core values.
        """
        return moral_compass
