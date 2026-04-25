"""
Translator tools — translate text between multiple languages.
"""

def register(mcp):

    @mcp.tool()
    def translate_text(text: str, target_language: str) -> str:
        """
        Translates a block of text into the specified language.
        Use this for the 'Mentor' or 'Translator' protocols.
        """
        # The LLM itself handles the translation, the tool is a way to trigger it formally.
        return f"[Translation Request] Target: {target_language}. Content: {text}"

    @mcp.tool()
    def get_common_phrases(category: str, language: str) -> str:
        """
        Get common phrases in a target language for a specific category (e.g., 'technical', 'greeting').
        """
        return f"Fetching {category} terminology in {language}. I'll provide the briefing now, boss."
