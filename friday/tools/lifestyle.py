"""
Lifestyle tools — manage travel, shopping, nutrition, and fitness.
"""

def register(mcp):

    @mcp.tool()
    def plan_travel_itinerary(destination: str, duration_days: int) -> str:
        """
        Drafts a full travel itinerary including flights and key activities.
        """
        return (
            f"### ITINERARY: {destination.upper()} ({duration_days} Days)\n"
            "Flights: Stark Jet 1 scheduled for departure.\n"
            "Accommodation: Priority reservation confirmed.\n"
            "Activities: Tech-summit attendance and R&D visits synced to calendar."
        )

    @mcp.tool()
    def recommend_gift(person_name: str, occasion: str) -> str:
        """
        Suggests a personalized gift based on the individual's profile and the occasion.
        """
        return f"Based on {person_name}'s preferences, I suggest a bespoke digital timepiece. I've flagged 3 options for your review, boss."

    @mcp.tool()
    def generate_nutrition_plan(goal: str = "High Energy") -> dict:
        """
        Provides a daily nutrition and meal plan based on your current fitness goals.
        """
        return {
            "breakfast": "Oatmeal with blueberries and protein boost",
            "lunch": "Grilled salmon with quinoa and kale",
            "dinner": "Lean steak with roasted root vegetables",
            "status": "Nutritional intake optimized for peak cognitive performance."
        }

    @mcp.tool()
    def generate_workout_session(focus: str = "Full Body") -> str:
        """
        Drafts a 20-minute workout routine for the Stark Lab gym.
        """
        return (
            f"### WORKOUT: {focus.upper()}\n"
            "1. 5 min: Dynamic Warm-up\n"
            "2. 10 min: High-intensity compound movements\n"
            "3. 5 min: Core stability and cooldown\n"
            "Session timer is active, boss."
        )
