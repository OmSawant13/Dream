import logging
from .prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

logger = logging.getLogger("papper-engine")

class PlanningEngine:
    """The Logic: Preparing context and parsing LLM decisions."""
    def __init__(self, client):
        self.client = client

    async def generate_plan(self, task, current_view, history):
        """Prepare context and call the LLM."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add few-shot examples
        messages.extend(FEW_SHOT_EXAMPLES)
        
        # Current state
        prompt = f"Task: {task}\n\n{current_view}\n\nHistory:\n"
        for h in history[-5:]: # Last 5 actions for context
            prompt += f"- {h}\n"
            
        messages.append({"role": "user", "content": prompt})
        
        logger.info("Generating next steps...")
        return await self.client.get_plan(messages)
