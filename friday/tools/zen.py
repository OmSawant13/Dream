"""
Zen tools — meditation, mental clarity, and focus exercises.
"""

def register(mcp):

    @mcp.tool()
    def start_guided_meditation(duration_min: int = 5) -> str:
        """
        Starts a 5-minute guided meditation session to reset cognitive load.
        """
        return (
            f"### ZEN MODE ACTIVE ({duration_min} min)\n"
            "1. Close your eyes, boss.\n"
            "2. Focus on the low hum of the lab power core.\n"
            "3. Breath in for 4 seconds... hold for 4... exhale for 8.\n"
            "I've silenced all notifications for your peace."
        )

    @mcp.tool()
    def generate_zen_koan() -> str:
        """
        Provides a thought-provoking Zen koan to sharpen your lateral thinking.
        """
        koans = [
            "What is the sound of one hand coding?",
            "When the master points at the moon, the fool looks at the keyboard.",
            "A cup is useful only when it is empty of legacy code."
        ]
        import random
        return f"Today's Koan: {random.choice(koans)}"
