"""
Configuration — load environment variables and app-wide settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Server identity
    SERVER_NAME: str = os.getenv("SERVER_NAME", "Friday")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

config = Config()
