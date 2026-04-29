import asyncio
import logging
from browser.observer import BrowserObserver
from browser.actions import BrowserActions
from planner.client import LLMClient
from planner.engine import PlanningEngine
from memory.trace import MemoryManager

logger = logging.getLogger("papper-agent")

class PapperAgent:
    """The Brain: Autonomous loop connecting perception, reasoning, and action."""
    def __init__(self, controller):
        self.controller = controller
        # FIX #1: Pass controller to observer
        self.observer = BrowserObserver(self.controller)
        self.actions = BrowserActions(self.controller, self.observer)
        
        self.client = LLMClient(provider="groq", model="llama-3.3-70b-versatile")
        self.planner = PlanningEngine(self.client)
        self.memory = MemoryManager()

    async def run(self, task, max_steps=15):
        """Execute the autonomous Observe-Plan-Act loop."""
        logger.info(f"🚀 Starting task: {task}")

        failed_plan_count = 0
        for step in range(max_steps):
            logger.info(f"--- STEP {step + 1} ---")

            # 1. OBSERVE
            # FIX #2: Correct method name capture_grid
            current_view = await self.observer.capture_grid()

            # 2. PLAN
            history = self.memory.history
            plan = await self.planner.generate_plan(task, current_view, history)

            if not plan:
                failed_plan_count += 1
                if failed_plan_count >= 3:
                    logger.error("❌ LLM failed to generate valid plan 3 times. Aborting task.")
                    return False
                logger.warning(f"Failed to generate plan (attempt {failed_plan_count}/3). Retrying...")
                continue

            failed_plan_count = 0  # Reset on successful plan
            logger.info(f"Thought: {plan.thought}")

            # 3. ACT
            for action in plan.actions:
                if action.action_type == "done":
                    logger.info("✅ Task completed according to agent.")
                    return True

                result = await self.execute_action(action)

                # 4. RECORD
                # FIX #2: Pydantic v2 compatibility - use model_dump() instead of dict()
                try:
                    action_dict = action.model_dump()
                except AttributeError:
                    action_dict = action.dict()  # Fallback for Pydantic v1
                self.memory.record_action(action_dict, result)

                if self.memory.is_stuck():
                    logger.warning("⚠️ Agent appears to be stuck in a loop. Aborting.")
                    return False

            await asyncio.sleep(1) # Breath between steps

        logger.warning("🛑 Max steps reached.")
        return False

    async def execute_action(self, action):
        """Route the action to the physical layer with safety checks."""
        a_type = action.action_type
        
        # SAFETY CHECK: Index validation
        if a_type in ["click", "type"] and action.index:
            if not self.observer.get_element(action.index):
                return {"status": "error", "message": f"Hallucinated index {action.index} - not in view."}

        if a_type == "click":
            return await self.actions.click_index(action.index)
        elif a_type == "type":
            return await self.actions.type_at_index(action.index, action.text)
        elif a_type == "scroll":
            return await self.actions.scroll(action.direction)
        elif a_type == "press_key":
            return await self.actions.press_key(action.text)
        elif a_type == "navigate":
            return await self.actions.navigate(action.url)
        elif a_type == "wait":
            logger.info(f"Waiting for {action.seconds} seconds...")
            await asyncio.sleep(action.seconds or 2)
            return {"status": "success", "message": f"Waited for {action.seconds}s"}
            
        return {"status": "error", "message": f"Unknown action type: {a_type}"}
