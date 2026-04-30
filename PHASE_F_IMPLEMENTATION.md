# PHASE F: Implementation Guide
**Date:** 2026-04-30  
**Status:** Ready to build  
**Target:** 4 weeks

---

## Overview

Phase F has 7 components across 3 bug fixes + 3 new files + 3 modified files.

| Component | File | Type | Complexity | Est. Time |
|-----------|------|------|-----------|-----------|
| StateVerifier | `agent/state_verifier.py` | NEW | Medium | 2 days |
| ContextBuilder | `agent/state_verifier.py` | NEW | Low | 1 day |
| LoopResolver | `agent/recovery_engine.py` | NEW | Medium | 2 days |
| BlockerHandler | `agent/blocker_handler.py` | NEW | Low | 1 day |
| Fix SQL LIMIT | `memory/persistent.py` | BUG FIX | Low | 1 day |
| Add cross-workflow check | `memory/persistent.py` | BUG FIX | Low | 1 day |
| Add helper methods | `memory/persistent.py` | MODIFY | Low | 1 day |
| Add state_context param | `planner/engine.py` | MODIFY | Low | 1 day |
| Add recovery prompt | `planner/prompts.py` | MODIFY | Low | 1 day |
| Full integration | `agent/agent.py` | MODIFY | High | 3 days |
| Tests | `test_phase_f.py` | NEW | Medium | 3 days |
| **TOTAL** | | | | **~16 days** |

---

## Build Order (Strict Sequence)

### Week 1: Foundation

#### Day 1: Fix SQL Bug (persistent.py)
```python
# CURRENT (broken):
rows = self.db.fetchall(
    """SELECT COUNT(*) as cnt FROM state_hashes
       WHERE workflow_id = ? AND visual_hash = ? AND text_hash = ?
       ORDER BY id DESC LIMIT ?""",
    (*params, lookback),
)

# NEW (fixed):
rows = self.db.fetchall(
    """SELECT COUNT(*) as cnt FROM state_hashes
       WHERE workflow_id = ? AND visual_hash = ? AND text_hash = ?
       AND id IN (
           SELECT id FROM state_hashes
           WHERE workflow_id = ?
           ORDER BY id DESC LIMIT ?
       )""",
    (workflow_id, visual_hash, text_hash, workflow_id, lookback),
)
```

**File:** `memory/persistent.py` line ~393  
**Test:** Run `test_phase_e_comprehensive.py` — must still be 8/8 PASS

---

#### Day 2-3: StateVerifier + ContextBuilder (NEW FILE)

**File:** `agent/state_verifier.py`

```python
from dataclasses import dataclass
from typing import Literal

ChangeType = Literal["NAVIGATION", "CONTENT", "UI_ONLY", "NO_CHANGE"]

@dataclass
class StateChange:
    change_type: ChangeType
    url_changed: bool
    visual_changed: bool
    text_changed: bool
    before_url: str
    after_url: str

class StateVerifier:
    def verify(self, before_url: str, after_url: str,
               before_visual: str, after_visual: str,
               before_text: str, after_text: str) -> StateChange:
        """Classify state change. Zero tokens — pure hash comparison."""
        url_changed = before_url != after_url
        visual_changed = before_visual != after_visual
        text_changed = before_text != after_text

        if url_changed:
            change_type = "NAVIGATION"
        elif text_changed:
            change_type = "CONTENT"
        elif visual_changed:
            change_type = "UI_ONLY"
        else:
            change_type = "NO_CHANGE"

        return StateChange(
            change_type=change_type,
            url_changed=url_changed,
            visual_changed=visual_changed,
            text_changed=text_changed,
            before_url=before_url,
            after_url=after_url,
        )

class ContextBuilder:
    _MESSAGES = {
        ("type",     "NO_CHANGE"):  "Last type had NO effect. Input may need Enter or Submit button to trigger.",
        ("type",     "CONTENT"):    "Last type updated page content as expected.",
        ("type",     "UI_ONLY"):    "Last type caused only visual change — content unchanged. Try pressing Enter.",
        ("click",    "NO_CHANGE"):  "Last click caused NO change. Element may be decorative or disabled. Try a different element.",
        ("click",    "NAVIGATION"): "Last click navigated to a new URL: {after_url}. Verify this is the correct destination.",
        ("click",    "CONTENT"):    "Last click updated page content (likely AJAX/modal). Check new elements in grid.",
        ("click",    "UI_ONLY"):    "Last click caused visual change only (hover/animation). Core content unchanged.",
        ("navigate", "NAVIGATION"): "Navigation succeeded. Now at: {after_url}.",
        ("navigate", "NO_CHANGE"):  "Navigation had no effect — URL may not have changed.",
        ("press_key","CONTENT"):    "Key press triggered content change. Check new elements.",
        ("press_key","NO_CHANGE"):  "Key press had no effect. Try a different approach.",
        ("scroll",   "CONTENT"):    "Scroll revealed new content.",
        ("scroll",   "NO_CHANGE"):  "Scroll had no effect — may be at bottom.",
    }

    def build(self, state_change: StateChange, action_type: str) -> str:
        """Convert state change to LLM context message."""
        key = (action_type, state_change.change_type)
        template = self._MESSAGES.get(key, f"Action resulted in: {state_change.change_type}.")
        msg = template.format(
            after_url=state_change.after_url,
            before_url=state_change.before_url,
        )
        return f"[STATE AFTER LAST ACTION]: {msg}"
```

**Tests to write:**
```python
def test_state_verifier_navigation():
    sv = StateVerifier()
    change = sv.verify("google.com", "amazon.com", "hash1", "hash1", "hash1", "hash1")
    assert change.change_type == "NAVIGATION"

def test_state_verifier_content():
    sv = StateVerifier()
    change = sv.verify("amazon.com", "amazon.com", "hash1", "hash1", "hash1", "hash2")
    assert change.change_type == "CONTENT"

def test_context_builder_no_change_type():
    cb = ContextBuilder()
    state = StateChange("NO_CHANGE", False, False, False, "url", "url")
    msg = cb.build(state, "type")
    assert "NO effect" in msg
```

---

#### Day 4-5: LoopResolver (NEW FILE)

**File:** `agent/recovery_engine.py`

```python
import logging
from planner.schema import AgentPlan

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

Respond with a SINGLE JSON action using the normal format.
Do not output multiple actions. Just ONE different action to try.
"""

class LoopResolver:
    def __init__(self, planning_engine):
        self.planner = planning_engine

    async def attempt_recovery(
        self,
        task: str,
        current_grid: str,
        stuck_actions: list[dict],
    ) -> AgentPlan | None:
        """
        Try to recover from a loop by asking LLM for a completely different approach.
        
        stuck_actions: list of recent actions that resulted in NO_CHANGE
        Returns: AgentPlan with recovery action, or None if recovery fails
        """
        stuck_summary = "\n".join(
            f"  - Step {a['step']}: {a['action_type']} → {a.get('state_change', 'NO_CHANGE')}"
            for a in stuck_actions[-3:]
        )
        
        prompt = RECOVERY_PROMPT_TEMPLATE.format(
            task=task,
            N=len(stuck_actions),
            stuck_summary=stuck_summary,
            current_grid=current_grid,
        )
        
        try:
            recovery_plan = await self.planner.generate_recovery_plan(prompt)
            logger.info(f"🔄 Recovery plan: {recovery_plan.thought}")
            return recovery_plan
        except Exception as e:
            logger.warning(f"❌ Recovery LLM call failed: {e}")
            return None
```

**Tests:**
```python
async def test_loop_resolver_creates_different_action():
    # Mock planner
    class MockPlanner:
        async def generate_recovery_plan(self, prompt):
            return AgentPlan(thought="Try Enter", actions=[...])
    
    resolver = LoopResolver(MockPlanner())
    stuck = [
        {"step": 1, "action_type": "type", "state_change": "NO_CHANGE"},
        {"step": 2, "action_type": "type", "state_change": "NO_CHANGE"},
        {"step": 3, "action_type": "type", "state_change": "NO_CHANGE"},
    ]
    
    plan = await resolver.attempt_recovery("test task", "[0] INPUT", stuck)
    assert plan is not None
    assert plan.thought is not None
```

---

### Week 2: Integration

#### Day 6-7: BlockerHandler (NEW FILE)

**File:** `agent/blocker_handler.py`

```python
import logging
from memory.persistent import PersistentMemory

logger = logging.getLogger("papper-blocker")

BLOCKER_KEYWORDS = {
    "cookie_banner": ["accept cookies", "cookie policy", "agree", "i accept", "accept all"],
    "modal": ["close", "dismiss", "×", "not now", "no thanks", "skip"],
    "paywall": ["subscribe", "sign up", "create account", "read more"],
    "captcha": ["verify you are human", "i'm not a robot", "captcha"],
    "rate_limit": ["too many requests", "slow down", "try again later"],
}

class BlockerHandler:
    def __init__(self, observer, actions, persistent_memory):
        self.observer = observer
        self.actions = actions
        self.persistent = persistent_memory

    async def detect_and_handle(self, grid_text: str, url: str) -> bool:
        """
        Detect blockers in grid and attempt to bypass.
        Returns True if blocker was handled, False if none detected or handling failed.
        """
        for blocker_type, keywords in BLOCKER_KEYWORDS.items():
            if any(kw.lower() in grid_text.lower() for kw in keywords):
                logger.info(f"🚫 Detected blocker: {blocker_type}")
                return await self._handle_blocker(blocker_type, url, grid_text)
        
        return False

    async def _handle_blocker(self, blocker_type: str, url: str, grid_text: str) -> bool:
        """Try known bypass, then heuristic bypass."""
        # Check for known bypass
        bypass = self.persistent.get_blocker_bypass(blocker_type, url)
        if bypass:
            logger.info(f"✅ Found known bypass for {blocker_type}")
            index = bypass.get("index")
            if index:
                result = await self.actions.click_index(str(index))
                if result.get("status") == "success":
                    self.persistent.record_blocker_outcome(blocker_type, url, success=True)
                    return True
        
        # Heuristic: find "close", "dismiss", "×", "accept" buttons
        for keyword in ["close", "dismiss", "×", "accept", "i agree", "skip"]:
            if keyword in grid_text.lower():
                logger.info(f"🔍 Trying heuristic: clicking '{keyword}'")
                # This is a simplified search; in practice, would need to find the element
                # For now, just return False as we'd need better element matching
                pass
        
        logger.warning(f"⚠️ Could not bypass {blocker_type}")
        return False
```

---

#### Day 8-9: Persistent.py Helper Methods

**File:** `memory/persistent.py`

Add 3 new methods:

```python
def check_cross_workflow_failure_signature(
    self, action_type: str, url: str, text_hash: str = None, threshold: int = 3
) -> bool:
    """Check if this action+state combo failed across ALL past workflows."""
    params = [action_type, "error", url]
    text_clause = ""
    if text_hash:
        text_clause = "AND sh.text_hash = ?"
        params.append(text_hash)
    
    rows = self.db.fetchall(
        f"""SELECT COUNT(*) as cnt FROM actions a
            JOIN state_hashes sh ON a.workflow_id = sh.workflow_id AND a.step = sh.step
            WHERE a.action_type = ? AND a.result_status = ?
            AND sh.url LIKE '%' || ? || '%'
            {text_clause}""",
        params,
    )
    return bool(rows and rows[0].get("cnt", 0) >= threshold)

def get_recent_actions_with_states(self, workflow_id: int, limit: int = 5) -> list[dict]:
    """Get recent actions with state info for recovery context."""
    return self.db.fetchall(
        """SELECT a.step, a.action_type, a.result_status, a.state_changed,
                  sh.url, sh.visual_hash, sh.text_hash
           FROM actions a
           LEFT JOIN state_hashes sh ON a.workflow_id = sh.workflow_id AND a.step = sh.step
           WHERE a.workflow_id = ?
           ORDER BY a.step DESC LIMIT ?""",
        (workflow_id, limit),
    )

def record_finding(self, workflow_id: int, key: str, value: str, step: int) -> None:
    """Record a semantic finding (Phase H TaskMemory integration point)."""
    # This is a stub for Phase H. For Phase F, we just pass.
    pass
```

---

#### Day 10: Planner Engine Modifications

**File:** `planner/engine.py`

```python
# CURRENT signature:
async def generate_plan(self, task, current_view, history, cbr_context=""):

# NEW signature:
async def generate_plan(self, task, current_view, history, cbr_context="", state_context=""):
    """Generate plan with optional state context from Phase F."""
    user_msg = build_user_prompt(task, current_view, history)
    
    if cbr_context:
        user_msg += f"\n\n{cbr_context}"
    
    if state_context:
        user_msg += f"\n\n{state_context}"  # Phase F addition
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,
        {"role": "user", "content": user_msg},
    ]
    
    return await self.client.get_plan(messages)

# NEW method:
async def generate_recovery_plan(self, recovery_prompt: str) -> AgentPlan:
    """One-shot recovery call for loop resolution."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": recovery_prompt},
    ]
    return await self.client.get_plan(messages)
```

---

#### Day 11: Prompts Update

**File:** `planner/prompts.py`

Add to SYSTEM_PROMPT:

```python
SYSTEM_PROMPT = """... [existing content] ...

## PHASE F: State Change Context

When you see [STATE AFTER LAST ACTION]: in the prompt, use it to understand
what your previous action actually accomplished. This is crucial feedback:

- If it says NO_CHANGE: your action had no visible effect. Do NOT repeat it.
  Choose a fundamentally different approach (different button, different input, navigate elsewhere).
- If it says NAVIGATION: you successfully moved to a new page. Proceed with new content.
- If it says CONTENT: your action updated the page content. Look for new elements.
- If it says UI_ONLY: visual change only (animation/hover). Core content unchanged.

IMPORTANT: NO_CHANGE means STOP and TRY SOMETHING DIFFERENT. Never repeat a failed action.
"""
```

---

### Week 3: Integration into Agent

#### Day 12-14: agent/agent.py Integration

**File:** `agent/agent.py` — MAJOR modifications

**1. Import Phase F components (top of file):**
```python
from agent.state_verifier import StateVerifier, ContextBuilder
from agent.recovery_engine import LoopResolver
from agent.blocker_handler import BlockerHandler
```

**2. Initialize in __init__:**
```python
def __init__(self, controller):
    # ... existing code ...
    self.state_verifier = StateVerifier()
    self.context_builder = ContextBuilder()
    self.loop_resolver = LoopResolver(self.planner)
    self.blocker_handler = BlockerHandler(self.observer, self.actions, self.persistent)
```

**3. In run() method, add state tracking at top:**
```python
async def run(self, task, max_steps=15):
    # ... existing setup ...
    
    last_state_context = ""  # Phase F
    stuck_actions = []       # Phase F
```

**4. OBSERVE phase — Capture state BEFORE loop check:**
```python
# After: current_view = await self.observer.capture_grid()
screenshot = await self.observer.capture_screenshot()
visual_hash = PersistentMemory.hash_visual(screenshot)
text_hash = PersistentMemory.hash_text(current_view)
url = await self._get_current_url()

self.persistent.record_state_hash(wf_id, step_counter, url,
                                 visual_hash=visual_hash,
                                 text_hash=text_hash)
```

**5. BLOCKER CHECK — Add before loop check:**
```python
# After state recording
blocker_handled = await self.blocker_handler.detect_and_handle(current_view, url)
if blocker_handled:
    logger.info("🚫 Blocker handled, continuing...")
    await asyncio.sleep(1)
    continue
```

**6. LOOP CHECK — Enhanced with recovery (CRITICAL):**
```python
is_repeated, repeat_count = self.persistent.is_state_repeated(
    wf_id, visual_hash=visual_hash, text_hash=text_hash
)

if is_repeated:
    logger.warning(f"🔁 State repeated {repeat_count} times")
    stuck_actions.append({
        "step": step_counter,
        "action_type": last_action_type if 'last_action_type' in dir() else "unknown",
        "state_change": "NO_CHANGE"
    })
    
    if repeat_count >= 3:
        logger.warning("⚡ Attempting loop recovery...")
        recent = self.persistent.get_recent_actions_with_states(wf_id, 3)
        recovery_plan = await self.loop_resolver.attempt_recovery(task, current_view, recent)
        
        if recovery_plan:
            logger.info("✅ Recovery plan found — executing")
            for r_action in recovery_plan.actions:
                await self.execute_action(r_action)
            last_state_context = ""  # Reset context
            continue  # Skip normal planning
        else:
            logger.error("🛑 Recovery failed. Hard abort.")
            self.persistent.complete_workflow(wf_id, success=False,
                total_steps=step_counter, notes="Aborted: loop + recovery failed")
            return False
```

**7. PLAN — Pass state_context:**
```python
# BEFORE:
plan = await self.planner.generate_plan(task, current_view, history, cbr_context=cbr_context)

# AFTER (Phase F):
plan = await self.planner.generate_plan(
    task, current_view, history,
    cbr_context=cbr_context,
    state_context=last_state_context,
)
```

**8. EXECUTE — Capture before/after and compute state change (CRITICAL):**
```python
for action in plan.actions:
    # BEFORE action
    pre_url = url
    pre_visual = visual_hash
    pre_text = text_hash
    
    last_action_type = action.action_type  # For stuck tracking
    result = await self.execute_action(action)
    
    # AFTER action — capture new state
    post_screenshot = await self.observer.capture_screenshot()
    post_view = await self.observer.capture_grid()
    post_url = await self._get_current_url()
    post_visual = PersistentMemory.hash_visual(post_screenshot)
    post_text = PersistentMemory.hash_text(post_view)
    
    # StateVerifier: classify change (Phase F — 0 tokens)
    state_change = self.state_verifier.verify(
        pre_url, post_url, pre_visual, post_visual, pre_text, post_text
    )
    
    # ContextBuilder: create LLM message for next step (Phase F — +60 tokens)
    last_state_context = self.context_builder.build(state_change, action.action_type)
    
    # Record with REAL state_changed value (Bug Fix #2)
    self.persistent.record_action(
        workflow_id=wf_id,
        step=step_counter,
        action_sequence=action_idx,
        action_dict=action.model_dump() if hasattr(action, 'model_dump') else action.dict(),
        result_dict=result,
        thought=plan.thought,
        url=url,
        state_changed=(state_change.text_changed or state_change.url_changed),  # Phase F fix
    )
    
    # Cross-workflow failure check (Bug Fix #3)
    if self.persistent.check_cross_workflow_failure_signature(action.action_type, post_url, post_text):
        logger.warning(f"⚠️ Cross-workflow failure detected for {action.action_type}")
```

---

### Week 4: Testing

#### Day 15-16: Tests + Verification

**File:** `test_phase_f.py`

```python
import asyncio
import pytest
from agent.state_verifier import StateVerifier, ContextBuilder, StateChange
from agent.recovery_engine import LoopResolver
from memory.persistent import PersistentMemory
from memory.db import DatabaseManager

class TestStateVerifier:
    def test_navigation(self):
        sv = StateVerifier()
        change = sv.verify("google.com", "amazon.com", "h1", "h1", "h1", "h1")
        assert change.change_type == "NAVIGATION"
    
    def test_content(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h1", "h1", "h2")
        assert change.change_type == "CONTENT"
    
    def test_ui_only(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h2", "h1", "h1")
        assert change.change_type == "UI_ONLY"
    
    def test_no_change(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h1", "h1", "h1")
        assert change.change_type == "NO_CHANGE"

class TestContextBuilder:
    def test_no_change_type_action(self):
        cb = ContextBuilder()
        state = StateChange("NO_CHANGE", False, False, False, "url", "url")
        msg = cb.build(state, "type")
        assert "NO effect" in msg
    
    def test_navigation_click_action(self):
        cb = ContextBuilder()
        state = StateChange("NAVIGATION", True, False, False, "url1", "url2")
        msg = cb.build(state, "click")
        assert "url2" in msg

class TestSQLLimitFix:
    def test_is_state_repeated_respects_lookback(self):
        """Verify the SQL LIMIT fix works."""
        db = DatabaseManager(':memory:')
        pm = PersistentMemory(db)
        
        wf_id = pm.start_workflow("test")
        
        # Create 10 states, match is at position 3 (old one)
        for i in range(10):
            visual = "match_hash" if i == 2 else f"hash_{i}"
            text = "match_hash" if i == 2 else f"text_{i}"
            pm.record_state_hash(wf_id, i+1, "url", visual, text)
        
        # Check with lookback=5 (should only see last 5 states, not the old match)
        is_repeated, count = pm.is_state_repeated(wf_id, "match_hash", "match_hash", lookback=5)
        
        # Should be False because match is outside the lookback window
        assert not is_repeated, "LIMIT bug not fixed: lookback not respected"

class TestCrossWorkflowFailure:
    def test_cross_workflow_failure_signature(self):
        """Verify cross-workflow failure detection works."""
        db = DatabaseManager(':memory:')
        pm = PersistentMemory(db)
        
        # Workflow 1: action failed
        wf1 = pm.start_workflow("task1")
        pm.record_action(wf1, 1, {"action_type": "click"}, {"status": "error"}, action_sequence=1)
        pm.record_state_hash(wf1, 1, "amazon.com/phones", "hash1", "hash1")
        pm.complete_workflow(wf1, False, 1)
        
        # Workflow 2: same action at same state
        wf2 = pm.start_workflow("task2")
        
        # Should detect cross-workflow failure
        has_failure = pm.check_cross_workflow_failure_signature("click", "amazon.com", "hash1")
        assert has_failure, "Cross-workflow failure not detected"

# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Final Checklist:**
- [ ] Phase E tests still 8/8 PASS
- [ ] StateVerifier tests PASS (4 change types)
- [ ] ContextBuilder tests PASS (message generation)
- [ ] SQL LIMIT fix verified
- [ ] Cross-workflow failure check verified
- [ ] LoopResolver integration test
- [ ] BlockerHandler integration test
- [ ] agent.py integration compiles without errors
- [ ] Manual task test: "Go to Google, search 'Python', click first result"

---

## Integration Checklist

After implementation, verify:

- [ ] `agent/state_verifier.py` exists with StateVerifier + ContextBuilder
- [ ] `agent/recovery_engine.py` exists with LoopResolver
- [ ] `agent/blocker_handler.py` exists with BlockerHandler
- [ ] `memory/persistent.py` has SQL fix + 3 new methods
- [ ] `planner/engine.py` has state_context param + generate_recovery_plan()
- [ ] `planner/prompts.py` has state context rule
- [ ] `agent/agent.py` has full Phase F integration
- [ ] `test_phase_f.py` has 8+ passing tests
- [ ] Phase E tests still pass (regression check)
- [ ] Manual smoke test completes successfully

---

## Success Definition

Phase F is complete when:

✅ **No loops** — agent can escape loops via recovery call  
✅ **Better decisions** — LLM sees state change context every step  
✅ **Blockers handled** — cookie banners auto-dismiss  
✅ **Bug fixes applied** — SQL LIMIT, state_changed, cross-workflow  
✅ **Tests passing** — 8/8 Phase F tests + 8/8 Phase E regression  
✅ **Smoke test** — simple 5-step task completes 90% of time  

Estimated effort: **4 weeks, 1 developer**
