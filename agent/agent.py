import asyncio
import logging
import os
from dotenv import load_dotenv
from browser.observer import BrowserObserver
from browser.actions import BrowserActions
from planner.client import LLMClient
from planner.engine import PlanningEngine
from memory.trace import MemoryManager
from memory.persistent import PersistentMemory

load_dotenv()
logger = logging.getLogger("papper-agent")

class PapperAgent:
    """The Brain: Autonomous loop connecting perception, reasoning, and action.
    
    Level 3 upgrade: Integrates PersistentMemory (Phase E) for cross-session
    learning, pattern recall, blocker bypass, and loop detection via state hashing.
    """
    def __init__(self, controller):
        self.controller = controller
        # FIX #1: Pass controller to observer
        self.observer = BrowserObserver(self.controller)
        self.actions = BrowserActions(self.controller, self.observer)
        
        provider = os.getenv("LLM_PROVIDER", "openrouter")
        model = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")
        self.client = LLMClient(provider=provider, model=model)
        self.planner = PlanningEngine(self.client)

        # Level 2: ephemeral memory (still used for in-session history display)
        self.memory = MemoryManager()

        # Level 3 Phase E: persistent cross-session memory
        self.persistent = PersistentMemory()

    async def run(self, task, max_steps=15):
        """Execute the autonomous Observe-Plan-Act loop with persistent memory."""
        logger.info(f"🚀 Starting task: {task}")

        # ── Phase E: Start workflow tracking ──
        wf_id = self.persistent.start_workflow(task)

        # ── Phase E: Recall similar past workflows ──
        similar = self.persistent.get_similar_workflows(task)
        if similar:
            best = similar[0]
            logger.info(
                f"📚 Found similar past task: \"{best['task_name']}\" "
                f"(similarity={best['similarity']}, success={best['success']})"
            )

        # ── Phase E: CBR context for LLM ──
        cbr_context = self.persistent.get_cbr_context(task)

        failed_plan_count = 0
        step_counter = 0

        for step in range(max_steps):
            logger.info(f"--- STEP {step + 1} ---")
            step_counter = step + 1

            # 1. OBSERVE
            # FIX #2: Correct method name capture_grid
            current_view = await self.observer.capture_grid()

            # ── Phase E: Capture state (visual + text) for Phase F ──
            screenshot = await self.observer.capture_screenshot()
            visual_hash = PersistentMemory.hash_visual(screenshot)
            text_hash = PersistentMemory.hash_text(current_view)
            url = await self._get_current_url()

            # ── Phase E: Record state hash (both visual + text) ──
            self.persistent.record_state_hash(wf_id, step_counter, url,
                                             visual_hash=visual_hash,
                                             text_hash=text_hash)

            # ── Phase E: Loop detection via state hashing (strict: both hashes must match) ──
            is_repeated, repeat_count = self.persistent.is_state_repeated(
                wf_id, visual_hash=visual_hash, text_hash=text_hash
            )
            if is_repeated:
                logger.warning(
                    f"🔁 State repeated {repeat_count} times — possible loop detected."
                )
                if repeat_count >= 3:
                    logger.error("🛑 Hard loop detected (3+ identical states). Aborting.")
                    self.persistent.complete_workflow(wf_id, success=False,
                                                      total_steps=step_counter,
                                                      notes="Aborted: state loop")
                    return False

            # ── Phase E: Check for known pattern ──
            pattern = self.persistent.detect_pattern(wf_id)
            if pattern and pattern["success_rate"] > 0.7:
                logger.info(
                    f"🧩 Pattern match: {pattern['pattern_type']} "
                    f"(success rate: {pattern['success_rate']})"
                )

            # 2. PLAN (with CBR context injected)
            history = self.memory.history
            plan = await self.planner.generate_plan(
                task, current_view, history, cbr_context=cbr_context
            )

            if not plan:
                failed_plan_count += 1
                if failed_plan_count >= 3:
                    logger.error("❌ LLM failed to generate valid plan 3 times. Aborting task.")
                    self.persistent.complete_workflow(wf_id, success=False,
                                                      total_steps=step_counter,
                                                      notes="Aborted: 3 failed plans")
                    return False
                logger.warning(f"Failed to generate plan (attempt {failed_plan_count}/3). Retrying...")
                continue

            failed_plan_count = 0  # Reset on successful plan
            logger.info(f"Thought: {plan.thought}")

            # 3. ACT
            for action in plan.actions:
                if action.action_type == "done":
                    logger.info("✅ Task completed according to agent.")

                    # ── Phase E: Record success & learn pattern ──
                    self.persistent.complete_workflow(wf_id, success=True,
                                                      total_steps=step_counter)
                    self._learn_from_run(wf_id)
                    return True

                # ── Phase E: Check failure signature before executing ──
                if self.persistent.check_failure_signature(
                    wf_id, action.action_type, url, text_hash
                ):
                    logger.warning(
                        f"⚠️ Failure signature: {action.action_type} at this state "
                        f"has failed 2+ times. Skipping."
                    )
                    continue

                result = await self.execute_action(action)

                # 4. RECORD (ephemeral)
                # FIX #2: Pydantic v2 compatibility - use model_dump() instead of dict()
                try:
                    action_dict = action.model_dump()
                except AttributeError:
                    action_dict = action.dict()  # Fallback for Pydantic v1

                self.memory.record_action(action_dict, result)

                # ── Phase E: Record to persistent DB ──
                for action_idx, act in enumerate(plan.actions, start=1):
                    # We only record the action that actually executed
                    if act == action:
                        self.persistent.record_action(
                            workflow_id=wf_id,
                            step=step_counter,
                            action_sequence=action_idx,
                            action_dict=action_dict,
                            result_dict=result,
                            thought=plan.thought,
                            url=url,
                        )
                
                # Level 2 stuck detection (still works)
                if self.memory.is_stuck():
                    logger.warning("⚠️ Agent appears to be stuck in a loop. Aborting.")
                    self.persistent.complete_workflow(wf_id, success=False,
                                                      total_steps=step_counter,
                                                      notes="Aborted: stuck loop (L2)")
                    return False

            await asyncio.sleep(1) # Breath between steps

        logger.warning("🛑 Max steps reached.")
        self.persistent.complete_workflow(wf_id, success=False,
                                          total_steps=step_counter,
                                          notes="Max steps reached")
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

    # ------------------------------------------------------------------
    # Phase E internals
    # ------------------------------------------------------------------

    async def _get_current_url(self):
        """Get the current browser URL safely."""
        try:
            page = await self.controller.get_active_page()
            return page.url
        except Exception:
            return "unknown"

    def _learn_from_run(self, workflow_id):
        """After a successful workflow, extract and store patterns.
        
        Looks at the action sequence and registers it as a reusable pattern.
        """
        actions = self.persistent.get_workflow_actions(workflow_id)
        if len(actions) < 2:
            return

        # Build the action type sequence
        action_types = [a["action_type"] for a in actions if a["result_status"] == "success"]
        if len(action_types) < 2:
            return

        # Infer a rough pattern_type from the first few actions
        if "navigate" in action_types[:2]:
            pattern_type = "navigation"
        elif "type" in action_types[:3]:
            pattern_type = "search"
        else:
            pattern_type = "general"

        # Store the successful sequence (capped at 6 actions)
        self.persistent.learn_pattern(
            pattern_type=pattern_type,
            action_sequence=action_types[:6],
            recommended_next=action_types[1:7] if len(action_types) > 1 else [],
            success=True,
        )
