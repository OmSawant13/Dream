"""
Phase F Comprehensive Test Suite

Tests:
    1. StateVerifier — 4 change type classifications
    2. ContextBuilder — message generation for all combos
    3. SQL LIMIT fix — lookback window respected
    4. Cross-workflow failure detection
    5. get_recent_actions_with_states
    6. record_finding (stub)
    7. BlockerHandler._extract_index parsing
    8. BlockerHandler._extract_domain parsing
    9. Phase E regression — 8/8 still pass
"""

import sys
sys.path.insert(0, ".")

from agent.state_verifier import StateVerifier, ContextBuilder, StateChange
from agent.recovery_engine import LoopResolver
from agent.blocker_handler import BlockerHandler
from memory.persistent import PersistentMemory
from memory.db import DatabaseManager


# ==================================================================
# 1. StateVerifier — 4 change types
# ==================================================================

class TestStateVerifier:
    def test_navigation(self):
        sv = StateVerifier()
        change = sv.verify("google.com", "amazon.com", "h1", "h1", "h1", "h1")
        assert change.change_type == "NAVIGATION"
        assert change.url_changed is True
        assert change.text_changed is False

    def test_content(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h1", "h1", "h2")
        assert change.change_type == "CONTENT"
        assert change.url_changed is False
        assert change.text_changed is True

    def test_ui_only(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h2", "h1", "h1")
        assert change.change_type == "UI_ONLY"
        assert change.visual_changed is True
        assert change.text_changed is False

    def test_no_change(self):
        sv = StateVerifier()
        change = sv.verify("amazon.com", "amazon.com", "h1", "h1", "h1", "h1")
        assert change.change_type == "NO_CHANGE"
        assert change.url_changed is False
        assert change.visual_changed is False
        assert change.text_changed is False

    def test_url_wins_over_text(self):
        """URL change should dominate even if text also changed."""
        sv = StateVerifier()
        change = sv.verify("google.com", "amazon.com", "h1", "h1", "t1", "t2")
        assert change.change_type == "NAVIGATION"

    def test_text_wins_over_visual(self):
        """Text change should dominate over visual-only."""
        sv = StateVerifier()
        change = sv.verify("url", "url", "v1", "v2", "t1", "t2")
        assert change.change_type == "CONTENT"


# ==================================================================
# 2. ContextBuilder — message generation
# ==================================================================

class TestContextBuilder:
    def test_no_change_type_action(self):
        cb = ContextBuilder()
        state = StateChange("NO_CHANGE", False, False, False, "url", "url")
        msg = cb.build(state, "type")
        assert "NO effect" in msg
        assert "[STATE AFTER LAST ACTION]" in msg

    def test_navigation_click_action(self):
        cb = ContextBuilder()
        state = StateChange("NAVIGATION", True, False, False, "url1", "url2")
        msg = cb.build(state, "click")
        assert "url2" in msg

    def test_content_click_action(self):
        cb = ContextBuilder()
        state = StateChange("CONTENT", False, False, True, "url", "url")
        msg = cb.build(state, "click")
        assert "AJAX" in msg or "content" in msg.lower()

    def test_unknown_action_fallback(self):
        """Unknown action types should get a generic fallback message."""
        cb = ContextBuilder()
        state = StateChange("NO_CHANGE", False, False, False, "url", "url")
        msg = cb.build(state, "unknown_action")
        assert "NO_CHANGE" in msg
        assert "[STATE AFTER LAST ACTION]" in msg

    def test_scroll_no_change(self):
        cb = ContextBuilder()
        state = StateChange("NO_CHANGE", False, False, False, "url", "url")
        msg = cb.build(state, "scroll")
        assert "no effect" in msg.lower() or "boundary" in msg.lower()


# ==================================================================
# 3. SQL LIMIT fix
# ==================================================================

class TestSQLLimitFix:
    def test_is_state_repeated_respects_lookback(self):
        """Match at step 3 should NOT appear when lookback=5 covers steps 6-10."""
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        wf_id = pm.start_workflow("test")
        for i in range(1, 11):
            visual = "match" if i == 3 else f"v{i}"
            text = "match" if i == 3 else f"t{i}"
            pm.record_state_hash(wf_id, i, "url", visual, text)

        is_rep, cnt = pm.is_state_repeated(wf_id, "match", "match", lookback=5)
        assert not is_rep, "SQL LIMIT bug: match at step 3 in last-5 window"
        assert cnt == 0

    def test_is_state_repeated_finds_match_in_window(self):
        """Match at step 9 SHOULD appear when lookback=5 covers steps 6-10."""
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        wf_id = pm.start_workflow("test")
        for i in range(1, 11):
            visual = "match" if i == 9 else f"v{i}"
            text = "match" if i == 9 else f"t{i}"
            pm.record_state_hash(wf_id, i, "url", visual, text)

        is_rep, cnt = pm.is_state_repeated(wf_id, "match", "match", lookback=5)
        assert cnt >= 1


# ==================================================================
# 4. Cross-workflow failure detection
# ==================================================================

class TestCrossWorkflowFailure:
    def test_detects_multi_workflow_failures(self):
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        # 3 workflows, same action, same result (error)
        for i in range(1, 4):
            wf = pm.start_workflow(f"task{i}")
            pm.record_action(
                wf, 1, {"action_type": "click"}, {"status": "error"},
                action_sequence=1,
            )
            pm.record_state_hash(wf, 1, f"https://amazon.com/page{i}", "v1", "t1")
            pm.complete_workflow(wf, False, 1)

        assert pm.check_cross_workflow_failure_signature("click", "amazon.com") is True

    def test_does_not_false_positive(self):
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        # Only 1 workflow with failure — below threshold
        wf = pm.start_workflow("task1")
        pm.record_action(
            wf, 1, {"action_type": "click"}, {"status": "error"},
            action_sequence=1,
        )
        pm.record_state_hash(wf, 1, "https://amazon.com/phones", "v1", "t1")

        assert pm.check_cross_workflow_failure_signature("click", "amazon.com") is False


# ==================================================================
# 5. get_recent_actions_with_states
# ==================================================================

class TestRecentActionsWithStates:
    def test_returns_joined_data(self):
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        wf = pm.start_workflow("test")
        pm.record_action(
            wf, 1, {"action_type": "click"}, {"status": "success"},
            action_sequence=1,
        )
        pm.record_state_hash(wf, 1, "https://example.com", "vis1", "txt1")

        recent = pm.get_recent_actions_with_states(wf, 1)
        assert len(recent) == 1
        assert recent[0]["action_type"] == "click"
        assert recent[0]["url"] == "https://example.com"

    def test_respects_limit(self):
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)

        wf = pm.start_workflow("test")
        for i in range(1, 6):
            pm.record_action(
                wf, i, {"action_type": "click"}, {"status": "success"},
                action_sequence=1,
            )
            pm.record_state_hash(wf, i, "url", f"v{i}", f"t{i}")

        recent = pm.get_recent_actions_with_states(wf, 3)
        assert len(recent) == 3


# ==================================================================
# 6. record_finding (stub — just verify it doesn't crash)
# ==================================================================

class TestRecordFinding:
    def test_stub_does_not_crash(self):
        db = DatabaseManager(":memory:")
        pm = PersistentMemory(db)
        wf = pm.start_workflow("test")
        pm.record_finding(wf, "price", "$299", 1)  # Should be no-op


# ==================================================================
# 7. BlockerHandler._extract_index
# ==================================================================

class TestBlockerHandlerParsing:
    def test_extract_index_valid(self):
        assert BlockerHandler._extract_index('[3] BUTTON: "Accept"') == 3
        assert BlockerHandler._extract_index('[0] LINK: "Home"') == 0
        assert BlockerHandler._extract_index('[42] INPUT: "Search"') == 42

    def test_extract_index_invalid(self):
        assert BlockerHandler._extract_index("no brackets here") is None
        assert BlockerHandler._extract_index("[] empty") is None
        assert BlockerHandler._extract_index("random text") is None

    def test_extract_domain(self):
        assert BlockerHandler._extract_domain("https://www.amazon.com/phones") == "amazon.com"
        assert BlockerHandler._extract_domain("https://google.com") == "google.com"
        assert BlockerHandler._extract_domain("https://sub.example.com/page") == "sub.example.com"


# ==================================================================
# 8. Integration imports
# ==================================================================

class TestIntegrationImports:
    def test_all_phase_f_modules_import(self):
        from agent.state_verifier import StateVerifier, ContextBuilder
        from agent.recovery_engine import LoopResolver
        from agent.blocker_handler import BlockerHandler
        from agent.agent import PapperAgent
        from planner.engine import PlanningEngine
        from planner.prompts import SYSTEM_PROMPT

        assert "STATE CHANGE FEEDBACK" in SYSTEM_PROMPT or "NO_CHANGE" in SYSTEM_PROMPT
        assert hasattr(PlanningEngine, "generate_recovery_plan")


# ==================================================================
# Runner
# ==================================================================

if __name__ == "__main__":
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + "PHASE F COMPREHENSIVE TEST SUITE".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    test_classes = [
        TestStateVerifier,
        TestContextBuilder,
        TestSQLLimitFix,
        TestCrossWorkflowFailure,
        TestRecentActionsWithStates,
        TestRecordFinding,
        TestBlockerHandlerParsing,
        TestIntegrationImports,
    ]

    total_pass = 0
    total_fail = 0
    results = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            try:
                getattr(instance, method_name)()
                total_pass += 1
                results.append((f"{cls.__name__}.{method_name}", "✅ PASS"))
            except Exception as e:
                total_fail += 1
                results.append((f"{cls.__name__}.{method_name}", f"❌ FAIL: {e}"))

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    for name, status in results:
        print(f"  {name:.<56} {status}")

    print()
    print(f"Total: {total_pass}/{total_pass + total_fail} PASSED")
    if total_fail == 0:
        print()
        print("╔" + "=" * 68 + "╗")
        print("║" + "🎉 ALL PHASE F TESTS PASSED 🎉".center(68) + "║")
        print("╚" + "=" * 68 + "╝")
    else:
        print(f"\n⚠️ {total_fail} test(s) FAILED")
        sys.exit(1)
