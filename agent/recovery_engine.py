"""
Phase F: Loop Recovery Engine

When the agent detects 3+ identical states (a confirmed loop), this module
takes over. Instead of aborting, it asks the LLM to choose a COMPLETELY
DIFFERENT strategy — with full context about what has already been tried.

Design rationale (from MemGPT/AutoGPT research):
    - Naive retry = doing the same thing and expecting different results.
    - Recovery = showing the LLM exactly what failed and forcing divergence.

The LoopResolver is a one-shot intervention: it fires once, and if the
recovery action also results in NO_CHANGE, the agent hard-aborts.
"""

import logging

logger = logging.getLogger("papper-recovery")

RECOVERY_PROMPT_TEMPLATE = """You are a browser agent that is STUCK in a loop on this task:

TASK: {task}

You have tried the following actions {N} times and ended up in the SAME browser state each time:
{stuck_summary}

Current browser grid:
{current_grid}

The above approaches are NOT working. You must choose a COMPLETELY DIFFERENT strategy:
- If you were clicking links: try navigating directly to the target URL instead
- If you were typing but nothing happened: try clicking a different input first, or press Enter
- If you navigated to a wrong page: use navigate action to go directly to the correct URL
- If a modal/popup is blocking: find and close it first
- If scrolling didn't help: try navigating to a more specific URL

CRITICAL: Do NOT repeat any of the failed actions listed above.

Respond with a SINGLE JSON action using the normal format.
Do not output multiple actions. Just ONE different action to try.
"""


class LoopResolver:
    """Strategic recovery from detected execution loops.

    This is NOT a general-purpose planner. It only fires when the
    StateVerifier has confirmed 3+ identical states, meaning the
    normal planning loop has failed to make progress.

    Flow:
        1. Agent detects loop (3+ NO_CHANGE states)
        2. Agent calls LoopResolver.attempt_recovery()
        3. LoopResolver builds a prompt with:
           - What was tried (stuck_actions summary)
           - Current page state (grid)
           - Explicit instruction to diverge
        4. LLM returns a recovery plan (or None on failure)
        5. Agent executes the recovery action
        6. If recovery ALSO results in NO_CHANGE → hard abort
    """

    def __init__(self, planning_engine):
        self.planner = planning_engine

    async def attempt_recovery(
        self,
        task: str,
        current_grid: str,
        stuck_actions: list[dict],
    ):
        """Try to recover from a loop by asking LLM for a different approach.

        Args:
            task: The original task description
            current_grid: Current browser grid text
            stuck_actions: Recent actions that resulted in NO_CHANGE
                Each dict has: step, action_type, state_change, url, result_status

        Returns:
            AgentPlan with recovery action, or None if recovery fails
        """
        if not stuck_actions:
            logger.warning("LoopResolver called with empty stuck_actions — skipping")
            return None

        # Build a human-readable summary of what failed
        stuck_summary = "\n".join(
            f"  - Step {a.get('step', '?')}: {a.get('action_type', '?')} "
            f"at {a.get('url', 'unknown')} → {a.get('state_changed', 'NO_CHANGE')}"
            for a in stuck_actions[-5:]  # Last 5 stuck actions max
        )

        prompt = RECOVERY_PROMPT_TEMPLATE.format(
            task=task,
            N=len(stuck_actions),
            stuck_summary=stuck_summary,
            current_grid=current_grid[:3000],  # Cap grid to avoid token waste
        )

        try:
            recovery_plan = await self.planner.generate_recovery_plan(prompt)
            if recovery_plan:
                logger.info(f"🔄 Recovery plan generated: {recovery_plan.thought}")
            return recovery_plan
        except Exception as e:
            logger.error(f"❌ Recovery LLM call failed: {e}")
            return None
