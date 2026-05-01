"""
Papper Agent — Phase F: Deterministic State Verification

The Brain: Autonomous loop connecting perception, reasoning, and action.

Phase E gave us persistent memory (cross-session learning).
Phase F gives us deterministic state verification:
    - Every action's outcome is classified (NAVIGATION/CONTENT/UI_ONLY/NO_CHANGE)
    - The LLM receives feedback about what its last action actually did
    - Loops are broken by the LoopResolver (strategic recovery, not blind retry)
    - Blockers (cookies, modals) are handled autonomously before planning
"""

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

# Phase F imports
from agent.state_verifier import StateVerifier, ContextBuilder
from agent.recovery_engine import LoopResolver
from agent.blocker_handler import BlockerHandler

load_dotenv()
logger = logging.getLogger("papper-agent")


class PapperAgent:
    """The Brain: Autonomous loop connecting perception, reasoning, and action.
    
    Level 3 upgrade: Integrates PersistentMemory (Phase E) for cross-session
    learning, pattern recall, blocker bypass, and loop detection via state hashing.

    Phase F upgrade: Deterministic state verification, loop recovery, and
    autonomous blocker handling.
    """
    def __init__(self, controller):
        self.controller = controller
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

        # Phase F: Deterministic verification components
        self.state_verifier = StateVerifier()
        self.context_builder = ContextBuilder()
        self.loop_resolver = LoopResolver(self.planner)
        self.blocker_handler = BlockerHandler(
            self.observer, self.actions, self.persistent
        )

    async def run(self, task, max_steps=15):
        """Execute the autonomous Observe-Plan-Act loop with state verification.
        
        Phase F changes to the loop:
            1. BLOCKER CHECK runs before planning (auto-dismiss cookies/modals)
            2. State is captured BEFORE and AFTER every action
            3. StateVerifier classifies the transition
            4. ContextBuilder injects feedback into the next LLM call
            5. LoopResolver fires on 3+ identical states (recovery, not abort)
        """
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

        # ── Phase F: State tracking for the feedback loop ──
        last_state_context = ""   # Feedback message from previous action
        last_action_type = None   # For stuck tracking

        for step in range(max_steps):
            logger.info(f"--- STEP {step + 1} ---")
            step_counter = step + 1

            # ==============================================================
            # 1. OBSERVE — Capture current browser state
            # ==============================================================
            current_view = await self.observer.capture_grid()

            # Capture state hashes for comparison
            screenshot = await self.observer.capture_screenshot()
            visual_hash = PersistentMemory.hash_visual(screenshot)
            text_hash = PersistentMemory.hash_text(current_view)
            url = await self._get_current_url()

            # Record state hash (Phase E)
            self.persistent.record_state_hash(
                wf_id, step_counter, url,
                visual_hash=visual_hash,
                text_hash=text_hash,
            )

            # ==============================================================
            # 2. BLOCKER CHECK — Auto-handle cookies/modals BEFORE planning
            # ==============================================================
            blocker_handled = await self.blocker_handler.detect_and_handle(
                current_view, url
            )
            if blocker_handled:
                logger.info("🚫 Blocker handled — re-capturing state")
                await asyncio.sleep(1)
                continue  # Re-observe after blocker dismissal

            # ==============================================================
            # 3. LOOP CHECK — Enhanced with recovery (Phase F)
            # ==============================================================
            is_repeated, repeat_count = self.persistent.is_state_repeated(
                wf_id, visual_hash=visual_hash, text_hash=text_hash
            )

            if is_repeated:
                logger.warning(
                    f"🔁 State repeated {repeat_count} times — possible loop."
                )
                if repeat_count >= 3:
                    # Phase F: Try recovery instead of immediate abort
                    logger.warning("⚡ Attempting loop recovery...")
                    recent = self.persistent.get_recent_actions_with_states(
                        wf_id, limit=5
                    )
                    recovery_plan = await self.loop_resolver.attempt_recovery(
                        task, current_view, recent
                    )

                    if recovery_plan:
                        logger.info("✅ Recovery plan found — executing")
                        for r_action in recovery_plan.actions:
                            if r_action.action_type == "done":
                                continue  # Don't let recovery auto-complete
                            await self.execute_action(r_action)
                        last_state_context = ""  # Reset context after recovery
                        continue  # Re-enter loop with fresh observation

                    # Recovery failed → hard abort
                    logger.error("🛑 Recovery failed. Hard abort.")
                    self.persistent.complete_workflow(
                        wf_id, success=False,
                        total_steps=step_counter,
                        notes="Aborted: loop + recovery failed",
                    )
                    return False

            # ── Phase E: Check for known pattern ──
            pattern = self.persistent.detect_pattern(wf_id)
            if pattern and pattern["success_rate"] > 0.7:
                logger.info(
                    f"🧩 Pattern match: {pattern['pattern_type']} "
                    f"(success rate: {pattern['success_rate']})"
                )

            # ==============================================================
            # 4. PLAN — With state context feedback (Phase F)
            # ==============================================================
            history = self.memory.history
            plan = await self.planner.generate_plan(
                task, current_view, history,
                cbr_context=cbr_context,
                state_context=last_state_context,  # Phase F feedback
            )

            if not plan:
                failed_plan_count += 1
                if failed_plan_count >= 3:
                    logger.error("❌ LLM failed to generate valid plan 3 times. Aborting.")
                    self.persistent.complete_workflow(
                        wf_id, success=False,
                        total_steps=step_counter,
                        notes="Aborted: 3 failed plans",
                    )
                    return False
                logger.warning(
                    f"Failed to generate plan (attempt {failed_plan_count}/3). Retrying..."
                )
                continue

            failed_plan_count = 0
            logger.info(f"Thought: {plan.thought}")

            # ==============================================================
            # 5. ACT — Execute with before/after state verification (Phase F)
            # ==============================================================
            for action_idx, action in enumerate(plan.actions, start=1):
                if action.action_type == "done":
                    logger.info("✅ Task completed according to agent.")
                    self.persistent.complete_workflow(
                        wf_id, success=True, total_steps=step_counter
                    )
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

                # ── Phase F: Check cross-workflow failure ──
                if self.persistent.check_cross_workflow_failure_signature(
                    action.action_type, url, text_hash
                ):
                    logger.warning(
                        f"⚠️ Cross-workflow failure: {action.action_type} "
                        f"has failed at this URL across multiple tasks. Skipping."
                    )
                    continue

                # ── Phase F: Capture state BEFORE action ──
                pre_url = url
                pre_visual = visual_hash
                pre_text = text_hash

                last_action_type = action.action_type
                result = await self.execute_action(action)

                # ── Phase F: Capture state AFTER action ──
                await self._wait_for_stability()

                post_screenshot = await self.observer.capture_screenshot()
                post_view = await self.observer.capture_grid()
                post_url = await self._get_current_url()
                post_visual = PersistentMemory.hash_visual(post_screenshot)
                post_text = PersistentMemory.hash_text(post_view)

                # ── Phase F: Classify the state transition ──
                state_change = self.state_verifier.verify(
                    pre_url, post_url,
                    pre_visual, post_visual,
                    pre_text, post_text,
                )

                logger.info(
                    f"📊 State change: {state_change.change_type} "
                    f"(URL={state_change.url_changed}, "
                    f"Visual={state_change.visual_changed}, "
                    f"Text={state_change.text_changed})"
                )

                # ── Phase F: Build feedback for the NEXT planning call ──
                last_state_context = self.context_builder.build(
                    state_change, action.action_type
                )

                # Update current state to the post-action values
                # (so the next action in this batch uses fresh state)
                url = post_url
                visual_hash = post_visual
                text_hash = post_text

                # 6. RECORD (ephemeral)
                try:
                    action_dict = action.model_dump()
                except AttributeError:
                    action_dict = action.dict()

                self.memory.record_action(action_dict, result)

                # ── Phase E+F: Record to persistent DB with REAL state_changed ──
                self.persistent.record_action(
                    workflow_id=wf_id,
                    step=step_counter,
                    action_sequence=action_idx,
                    action_dict=action_dict,
                    result_dict=result,
                    thought=plan.thought,
                    url=pre_url,
                    state_changed=(
                        state_change.text_changed or state_change.url_changed
                    ),
                )
                
                # Level 2 stuck detection (still active as fallback)
                if self.memory.is_stuck():
                    logger.warning("⚠️ Agent appears to be stuck in a loop. Aborting.")
                    self.persistent.complete_workflow(
                        wf_id, success=False,
                        total_steps=step_counter,
                        notes="Aborted: stuck loop (L2)",
                    )
                    return False

            await asyncio.sleep(1)  # Breath between steps

        logger.warning("🛑 Max steps reached.")
        self.persistent.complete_workflow(
            wf_id, success=False,
            total_steps=step_counter,
            notes="Max steps reached",
        )
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

    # ------------------------------------------------------------------
    # Phase F internals
    # ------------------------------------------------------------------

    async def _wait_for_stability(self, max_wait_ms=2000, interval_ms=200):
        """Wait until the page content stops changing (DOM stability).
        
        Borrowed from Cypress/Playwright patterns. Prevents capturing
        state during animations or loading spinners.

        Takes two snapshots separated by interval_ms. If they match,
        the page is considered stable. Otherwise, keeps checking until
        max_wait_ms is reached.
        """
        start_time = asyncio.get_event_loop().time()
        
        # Take initial snapshot
        try:
            last_grid = await self.observer.capture_grid()
            last_hash = PersistentMemory.hash_text(last_grid)
        except Exception:
            return True  # If observation fails, don't block

        while (asyncio.get_event_loop().time() - start_time) < (max_wait_ms / 1000):
            await asyncio.sleep(interval_ms / 1000)
            
            try:
                curr_grid = await self.observer.capture_grid()
                curr_hash = PersistentMemory.hash_text(curr_grid)
            except Exception:
                return True

            if curr_hash == last_hash:
                return True  # Page is stable
            
            last_hash = curr_hash
            
        logger.debug("⏳ Page did not stabilize within timeout — proceeding anyway.")
        return False
