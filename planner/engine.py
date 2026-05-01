import logging
from .prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

logger = logging.getLogger("papper-engine")

class PlanningEngine:
    """The Logic: Preparing context and parsing LLM decisions."""
    def __init__(self, client):
        self.client = client

    async def generate_plan(self, task, current_view, history, cbr_context="", state_context=""):
        """Prepare context and call the LLM.
        
        Args:
            task: The user's task description
            current_view: Current browser grid
            history: List of recent action strings
            cbr_context: Phase E past-experience block to inject (optional).
            state_context: Phase F state change feedback (optional).
                Example: "[STATE AFTER LAST ACTION]: Last click caused NO change..."
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add few-shot examples
        messages.extend(FEW_SHOT_EXAMPLES)
        
        # Current state
        prompt = f"Task: {task}\n\n{current_view}\n\nHistory:\n"
        for h in history[-5:]: # Last 5 actions for context
            prompt += f"- {h}\n"

        # Phase E: Inject learned experience from past similar workflows
        if cbr_context:
            prompt += f"\n{cbr_context}\n"

        # Phase F: Inject state change feedback from last action
        # This is the critical feedback loop that prevents action repetition.
        if state_context:
            prompt += f"\n{state_context}\n"
            
        messages.append({"role": "user", "content": prompt})
        
        logger.info("Generating next steps...")
        return await self.client.get_plan(messages)

    async def generate_recovery_plan(self, recovery_prompt: str):
        """One-shot recovery call for loop resolution (Phase F).

        This is NOT the normal planning path. It's called exclusively by
        LoopResolver when the agent is confirmed stuck. The recovery prompt
        contains explicit instructions to diverge from failed strategies.

        Args:
            recovery_prompt: Fully formatted prompt from LoopResolver

        Returns:
            AgentPlan with recovery action, or None on failure
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": recovery_prompt},
        ]
        logger.info("🔄 Generating recovery plan...")
        return await self.client.get_plan(messages)

