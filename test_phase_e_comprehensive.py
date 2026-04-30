#!/usr/bin/env python3
"""
PHASE E COMPREHENSIVE VERIFICATION TEST
Tests: Visual hashing, state tracking, loop detection, pattern learning, blockers
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from memory.db import DatabaseManager
from memory.persistent import PersistentMemory
from memory.trace import MemoryManager
import hashlib

# ============================================================================
# TEST 1: VISUAL HASH CAPTURE AND COMPUTATION
# ============================================================================
def test_visual_hash():
    print("\n" + "="*70)
    print("TEST 1: VISUAL HASH COMPUTATION")
    print("="*70)

    # Simulate screenshot bytes
    screenshot_bytes_1 = b"fake_screenshot_data_v1"
    screenshot_bytes_2 = b"fake_screenshot_data_v1"  # Same
    screenshot_bytes_3 = b"fake_screenshot_data_v2"  # Different

    hash1 = PersistentMemory.hash_visual(screenshot_bytes_1)
    hash2 = PersistentMemory.hash_visual(screenshot_bytes_2)
    hash3 = PersistentMemory.hash_visual(screenshot_bytes_3)

    print(f"Hash 1 (v1): {hash1}")
    print(f"Hash 2 (v1): {hash2}")
    print(f"Hash 3 (v2): {hash3}")

    assert hash1 == hash2, "❌ FAIL: Same screenshots should have same hash"
    assert hash1 != hash3, "❌ FAIL: Different screenshots should have different hash"

    print("✅ PASS: Visual hashing works correctly")
    return True

# ============================================================================
# TEST 2: TEXT HASH COMPUTATION
# ============================================================================
def test_text_hash():
    print("\n" + "="*70)
    print("TEST 2: TEXT HASH COMPUTATION")
    print("="*70)

    text1 = "[0] BUTTON: 'Click me'\n[1] INPUT: 'Search'"
    text2 = "[0] BUTTON: 'Click me'\n[1] INPUT: 'Search'"  # Same
    text3 = "[0] BUTTON: 'Different'\n[1] INPUT: 'Search'"  # Different

    hash1 = PersistentMemory.hash_text(text1)
    hash2 = PersistentMemory.hash_text(text2)
    hash3 = PersistentMemory.hash_text(text3)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")

    assert hash1 == hash2, "❌ FAIL: Same text should have same hash"
    assert hash1 != hash3, "❌ FAIL: Different text should have different hash"

    print("✅ PASS: Text hashing works correctly")
    return True

# ============================================================================
# TEST 3: STATE HASH STORAGE (Database)
# ============================================================================
def test_state_hash_storage():
    print("\n" + "="*70)
    print("TEST 3: STATE HASH STORAGE IN DATABASE")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    # Start workflow
    wf_id = pm.start_workflow("test_task")
    print(f"Workflow ID: {wf_id}")

    # Record state with both hashes
    visual_hash = PersistentMemory.hash_visual(b"screenshot1")
    text_hash = PersistentMemory.hash_text("[0] BUTTON")
    url = "https://example.com"

    pm.record_state_hash(wf_id, step=1, url=url, visual_hash=visual_hash, text_hash=text_hash)
    print(f"Recorded state: step=1, visual_hash={visual_hash[:10]}..., text_hash={text_hash[:10]}...")

    # Query from database
    cursor = db.conn.cursor()
    cursor.execute("SELECT visual_hash, text_hash FROM state_hashes WHERE workflow_id=? AND step=?",
                   (wf_id, 1))
    result = cursor.fetchone()

    if not result:
        print("❌ FAIL: State hash not found in database!")
        return False

    stored_visual, stored_text = result
    print(f"Retrieved: visual_hash={stored_visual[:10] if stored_visual else 'None'}..., text_hash={stored_text[:10] if stored_text else 'None'}...")

    assert stored_visual == visual_hash, "❌ FAIL: Visual hash not stored correctly"
    assert stored_text == text_hash, "❌ FAIL: Text hash not stored correctly"

    print("✅ PASS: State hashes stored correctly in DB")
    return True

# ============================================================================
# TEST 4: LOOP DETECTION (AND LOGIC)
# ============================================================================
def test_loop_detection():
    print("\n" + "="*70)
    print("TEST 4: LOOP DETECTION (AND LOGIC)")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    wf_id = pm.start_workflow("loop_test")

    # Record same state 3 times
    visual_hash = PersistentMemory.hash_visual(b"screenshot")
    text_hash = PersistentMemory.hash_text("[0] BUTTON")

    for step in range(1, 4):
        pm.record_state_hash(wf_id, step=step, url="https://example.com",
                             visual_hash=visual_hash, text_hash=text_hash)

    # Test loop detection at step 3 (lookback=5 by default)
    is_repeated, repeat_count = pm.is_state_repeated(wf_id, visual_hash=visual_hash, text_hash=text_hash)

    print(f"State repeated: {is_repeated}, Count: {repeat_count}")

    assert is_repeated, f"❌ FAIL: Loop not detected! is_repeated={is_repeated}"
    assert repeat_count >= 2, f"❌ FAIL: Repeat count should be >= 2, got {repeat_count}"

    print("✅ PASS: Loop detection works with AND logic")

    # Test NO loop when only visual matches
    print("\n--- Test partial match (visual only) ---")
    different_text_hash = PersistentMemory.hash_text("[0] DIFFERENT")
    is_repeated2, _ = pm.is_state_repeated(wf_id, visual_hash=visual_hash, text_hash=different_text_hash)
    print(f"Visual only match - is_repeated: {is_repeated2}")
    assert not is_repeated2, "❌ FAIL: Should not detect loop when only visual matches (needs both)"

    print("✅ PASS: Loop detection requires BOTH hashes (AND logic)")
    return True

# ============================================================================
# TEST 5: PATTERN LEARNING
# ============================================================================
def test_pattern_learning():
    print("\n" + "="*70)
    print("TEST 5: PATTERN LEARNING")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    wf_id = pm.start_workflow("pattern_test")

    # Record actions for a workflow
    actions_sequence = ["navigate", "type", "click", "wait", "done"]

    for idx, action_type in enumerate(actions_sequence[:-1], start=1):
        action_dict = {"action_type": action_type, "index": idx}
        result_dict = {"status": "success"}
        pm.record_action(
            workflow_id=wf_id,
            step=1,
            action_dict=action_dict,
            result_dict=result_dict,
            action_sequence=idx
        )

    # Complete workflow (triggers learning)
    pm.complete_workflow(wf_id, success=True, total_steps=1)

    # Get workflow actions
    actions = pm.get_workflow_actions(wf_id)
    print(f"Recorded {len(actions)} actions")

    for action in actions:
        print(f"  - {action['action_type']} (seq={action.get('action_sequence', '?')})")

    assert len(actions) > 0, "❌ FAIL: No actions recorded"

    print("✅ PASS: Pattern learning records actions")
    return True

# ============================================================================
# TEST 6: BLOCKER MANAGEMENT
# ============================================================================
def test_blocker_management():
    print("\n" + "="*70)
    print("TEST 6: BLOCKER MANAGEMENT")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    # Learn a blocker (requires detection_rule and bypass_method as dicts)
    pm.learn_blocker(
        blocker_type="modal",
        url_pattern="example.com",
        detection_rule={"type": "xpath", "selector": "//div[@class='modal']"},
        bypass_method={"action": "click", "selector": ".close-button"}
    )
    print("✅ Blocker learned: modal on example.com")

    # Retrieve blocker
    bypass = pm.get_blocker_bypass("modal", "https://example.com/page")
    print(f"Bypass hint: {bypass}")

    assert bypass and isinstance(bypass, dict) and "action" in bypass, "❌ FAIL: Blocker not retrieved correctly"

    # Record blocker outcome
    pm.record_blocker_outcome("modal", "example.com", success=True)
    print("✅ Blocker outcome recorded")

    print("✅ PASS: Blocker management works")
    return True

# ============================================================================
# TEST 7: FAILURE SIGNATURE TRACKING
# ============================================================================
def test_failure_signature():
    print("\n" + "="*70)
    print("TEST 7: FAILURE SIGNATURE TRACKING")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    wf_id = pm.start_workflow("fail_test")
    visual_hash = PersistentMemory.hash_visual(b"screenshot")
    text_hash = PersistentMemory.hash_text("[0] BUTTON")

    # Record 2 failures of same action at same state
    for i in range(2):
        action_dict = {"action_type": "click", "index": 0}
        result_dict = {"status": "error", "message": "Element not found"}  # Must be "error" not "failure"
        pm.record_action(
            workflow_id=wf_id,
            step=i+1,
            action_dict=action_dict,
            result_dict=result_dict,
            action_sequence=1
        )
        pm.record_state_hash(wf_id, step=i+1, url="https://example.com",
                            visual_hash=visual_hash, text_hash=text_hash)

    # Check failure signature
    has_signature = pm.check_failure_signature(wf_id, "click", "https://example.com", text_hash)
    print(f"Failure signature detected: {has_signature}")

    assert has_signature, "❌ FAIL: Failure signature not detected"

    print("✅ PASS: Failure signature tracking works")
    return True

# ============================================================================
# TEST 8: CBR CONTEXT GENERATION
# ============================================================================
def test_cbr_context():
    print("\n" + "="*70)
    print("TEST 8: CBR CONTEXT GENERATION")
    print("="*70)

    db = DatabaseManager(':memory:')
    pm = PersistentMemory(db)

    # Create multiple successful workflows with different task names
    # (Need multiple tasks for TF-IDF similarity to work correctly)
    workflows = [
        ("navigate to amazon and buy laptop", 3),
        ("go to google search for python documentation", 4),
    ]

    for task_name, steps in workflows:
        wf_id = pm.start_workflow(task_name)

        # Add some actions
        for i in range(1, steps + 1):
            action_dict = {"action_type": "navigate" if i == 1 else "click", "index": i}
            result_dict = {"status": "success", "message": "OK"}
            pm.record_action(
                workflow_id=wf_id,
                step=i,
                action_dict=action_dict,
                result_dict=result_dict,
                action_sequence=1
            )

        pm.complete_workflow(wf_id, success=True, total_steps=steps)

    # Get CBR context - should find similar task
    context = pm.get_cbr_context("google search python")  # Overlaps with second workflow
    print(f"CBR Context: {context[:100] if context else 'Empty'}...")

    assert context, "❌ FAIL: CBR context not generated"

    print("✅ PASS: CBR context generation works")
    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
async def run_all_tests():
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "PHASE E COMPREHENSIVE VERIFICATION TEST" + " "*15 + "║")
    print("╚" + "="*68 + "╝")

    tests = [
        ("Visual Hash Computation", test_visual_hash),
        ("Text Hash Computation", test_text_hash),
        ("State Hash Storage", test_state_hash_storage),
        ("Loop Detection (AND Logic)", test_loop_detection),
        ("Pattern Learning", test_pattern_learning),
        ("Blocker Management", test_blocker_management),
        ("Failure Signature Tracking", test_failure_signature),
        ("CBR Context Generation", test_cbr_context),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            results.append((name, f"❌ ERROR: {str(e)[:50]}"))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for name, result in results:
        print(f"{name:.<50} {result}")

    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)

    print(f"\nTotal: {passed}/{total} PASSED")

    if passed == total:
        print("\n╔" + "="*68 + "╗")
        print("║" + " "*20 + "🎉 PHASE E IS VERIFIED! 🎉" + " "*20 + "║")
        print("║" + " "*18 + "ALL TESTS PASSED - READY FOR PHASE F" + " "*14 + "║")
        print("╚" + "="*68 + "╝\n")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review above for details.\n")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
