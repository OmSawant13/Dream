import json
import logging
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .schema import AgentPlan

load_dotenv()

logger = logging.getLogger("papper-client")

class LLMClient:
    """The Voice: Structured communication with LLMs (Groq, OpenAI, Ollama)."""
    def __init__(self, provider="ollama", model=None):
        self.provider = provider
        
        if provider == "groq":
            self.model = model or "llama-3.3-70b-versatile"
            self.client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY")
            )
        elif provider == "openai":
            self.model = model or "gpt-4o"
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else: # Default to Ollama
            self.model = model or "llama3.1:8b"
            self.client = AsyncOpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" # Dummy key for local
            )

    async def get_plan(self, messages):
        """Request a structured plan from the LLM."""
        try:
            # Add JSON response format requirement to the system message or via parameter
            # Groq and OpenAI support response_format={"type": "json_object"}
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"} if self.provider != "ollama" else None,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            logger.debug(f"LLM Raw Output: {content}")
            
            data = json.loads(content)
            
            # Validate with Pydantic
            return AgentPlan(**data)
                
        except Exception as e:
            logger.error(f"LLM Client Error ({self.provider}): {e}")
            if "api_key" in str(e).lower():
                logger.error("Check your API keys in the .env file.")
            return None
