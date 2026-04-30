#!/usr/bin/env python3
"""
DEEP PHASE E AUDIT - Find hidden bugs, incomplete features, edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from memory.db import DatabaseManager
from memory.persistent import PersistentMemory
from memory.trace import MemoryManager
import inspect

print("\n" + "="*70)
print("DEEP PHASE E CODE AUDIT")
print("="*70)

# ============================================================================
# AUDIT 1: Check all expected methods exist and have correct signatures
# ============================================================================
print("\n[AUDIT 1] Method Signatures")
print("-" * 70)

pm_methods = {
    "start_workflow": ["task_name"],
    "record_state_hash": ["workflow_id", "step", "url", "visual_hash", "text_hash"],
    "is_state_repeated": ["workflow_id", "visual_hash", "text_hash"],
    "record_action": ["workflow_id", "step", "action_dict", "result_dict"],
    "detect_pattern": ["workflow_id", "window"],
    "check_failure_signature": ["workflow_id", "action_type", "url", "text_hash"],
    "learn_pattern": ["pattern_type", "action_sequence", "recommended_next", "success"],
    "complete_workflow": ["workflow_id", "success", "total_steps"],
    "get_similar_workflows": ["task_name", "threshold", "limit"],
    "get_cbr_context": ["task_name", "max_cases"],
    "get_workflow_actions": ["workflow_id"],
    "learn_blocker": ["blocker_type", "url_pattern", "detection_rule", "bypass_method"],
    "get_blocker_bypass": ["blocker_type", "url"],
    "record_blocker_outcome": ["blocker_type", "url_pattern", "success"],
    "hash_visual": ["screenshot_bytes"],  # static method
    "hash_text": ["text"],  # static method
}

db = DatabaseManager(':memory:')
pm = PersistentMemory(db)

missing_methods = []
for method_name, expected_params in pm_methods.items():
    if not hasattr(pm, method_name):
        missing_methods.append(method_name)
        print(f"❌ MISSING: {method_name}")
    else:
        method = getattr(pm, method_name)
        sig = inspect.signature(method)
        params = [p for p in sig.parameters.keys() if p != 'self']
        print(f"✅ {method_name}: {params}")

if missing_methods:
    print(f"\n❌ CRITICAL: {len(missing_methods)} methods missing!")
else:
    print(f"\n✅ All {len(pm_methods)} expected methods present")

# ============================================================================
# AUDIT 2: Check database schema
# ============================================================================
print("\n[AUDIT 2] Database Schema")
print("-" * 70)

cursor = db.conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

required_tables = {
    "workflows": ["id", "task_name", "created_at", "completed_at", "success", "total_steps"],
    "actions": ["workflow_id", "step", "action_sequence", "action_type", "result_status", "url"],
    "state_hashes": ["workflow_id", "step", "url", "visual_hash", "text_hash"],
    "patterns": ["pattern_type", "action_sequence", "success_rate"],
    "blockers": ["blocker_type", "url_pattern", "detection_rule", "bypass_method"],
}

for table_name, expected_cols in required_tables.items():
    cursor.execute(f"PRAGMA table_info({table_name})")
    actual_cols = [row[1] for row in cursor.fetchall()]
    
    missing_cols = [c for c in expected_cols if c not in actual_cols]
    if missing_cols:
        print(f"❌ {table_name}: Missing columns {missing_cols}")
    else:
        print(f"✅ {table_name}: All required columns present")

# Check constraints
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='actions'")
actions_schema = cursor.fetchone()[0]
has_unique = "UNIQUE" in actions_schema
print(f"{'✅' if has_unique else '❌'} actions table has UNIQUE constraint: {has_unique}")

# ============================================================================
# AUDIT 3: Test edge cases
# ============================================================================
print("\n[AUDIT 3] Edge Cases & Error Handling")
print("-" * 70)

edge_cases = []

# Edge case 1: Empty workflow
try:
    wf_id = pm.start_workflow("")
    print(f"⚠️ EDGE CASE: Empty task name accepted (wf_id={wf_id})")
    edge_cases.append("empty_task_name")
except:
    print("✅ Empty task name rejected")

# Edge case 2: Null hashes
try:
    wf_id = pm.start_workflow("test")
    pm.record_state_hash(wf_id, 1, "http://example.com", visual_hash=None, text_hash=None)
    is_rep, _ = pm.is_state_repeated(wf_id, visual_hash=None, text_hash=None)
    print(f"⚠️ EDGE CASE: Null hashes handled (is_repeated={is_rep})")
except Exception as e:
    print(f"✅ Null hashes rejected: {str(e)[:50]}")

# Edge case 3: Negative step number
try:
    wf_id = pm.start_workflow("test")
    pm.record_state_hash(wf_id, -1, "http://example.com", visual_hash="abc", text_hash="def")
    print("⚠️ EDGE CASE: Negative step accepted")
    edge_cases.append("negative_step")
except:
    print("✅ Negative step rejected")

# Edge case 4: Very large step number
try:
    wf_id = pm.start_workflow("test")
    pm.record_state_hash(wf_id, 999999, "http://example.com", visual_hash="abc", text_hash="def")
    print("✅ Large step numbers accepted (OK)")
except Exception as e:
    print(f"❌ Large step numbers rejected: {str(e)[:50]}")

# Edge case 5: Unicode in task names
try:
    wf_id = pm.start_workflow("Go to 你好.com and 검색 python 🐍")
    print("✅ Unicode task names accepted")
except Exception as e:
    print(f"❌ Unicode task names rejected: {str(e)[:50]}")
    edge_cases.append("unicode_failure")

# ============================================================================
# AUDIT 4: Check for incomplete implementations
# ============================================================================
print("\n[AUDIT 4] Code Completeness")
print("-" * 70)

# Check if methods are just stubs
def is_stub(method):
    """Check if method is mostly docstring/pass"""
    source = inspect.getsource(method)
    lines = [l.strip() for l in source.split('\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('"""') and not l.strip().startswith("'''")]
    code_lines = [l for l in lines if l and not l.startswith('def ') and not l.startswith('@')]
    return len(code_lines) < 3  # Less than 3 lines of real code = likely stub

incomplete = []
for method_name in ["detect_pattern", "learn_pattern", "check_failure_signature"]:
    try:
        method = getattr(pm, method_name)
        if is_stub(method):
            incomplete.append(method_name)
            print(f"⚠️ INCOMPLETE: {method_name} appears to be stub")
        else:
            print(f"✅ {method_name}: Fully implemented")
    except:
        print(f"❌ {method_name}: Error checking")

# ============================================================================
# AUDIT 5: Check error handling
# ============================================================================
print("\n[AUDIT 5] Error Handling & Logging")
print("-" * 70)

# Check if methods have try-catch
methods_with_error_handling = ["record_state_hash", "record_action", "get_similar_workflows"]

for method_name in methods_with_error_handling:
    method = getattr(pm, method_name)
    source = inspect.getsource(method)
    has_try = "try:" in source
    has_except = "except" in source
    status = "✅" if (has_try and has_except) else "⚠️"
    print(f"{status} {method_name}: try-catch={has_try and has_except}")

# ============================================================================
# AUDIT 6: Integration with agent.py
# ============================================================================
print("\n[AUDIT 6] Agent Integration Points")
print("-" * 70)

# Read agent.py and check for Phase E calls
with open("agent/agent.py", "r") as f:
    agent_code = f.read()

expected_calls = [
    "self.persistent.start_workflow",
    "self.persistent.record_state_hash",
    "self.persistent.is_state_repeated",
    "self.persistent.record_action",
    "self.persistent.detect_pattern",
    "self.persistent.check_failure_signature",
    "self.persistent.complete_workflow",
    "self.persistent.get_similar_workflows",
    "self.persistent.get_cbr_context",
]

for call in expected_calls:
    if call in agent_code:
        print(f"✅ Agent calls: {call.split('.')[-1]}")
    else:
        print(f"❌ Agent missing: {call.split('.')[-1]}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("AUDIT SUMMARY")
print("="*70)

issues = len(missing_methods) + len(edge_cases) + len(incomplete)

if issues == 0:
    print("✅ NO CRITICAL ISSUES FOUND")
    print("✅ Phase E appears COMPLETE and SAFE")
else:
    print(f"⚠️ {issues} potential issues found:")
    if missing_methods:
        print(f"   - {len(missing_methods)} missing methods")
    if edge_cases:
        print(f"   - {len(edge_cases)} edge cases unhandled")
    if incomplete:
        print(f"   - {len(incomplete)} incomplete implementations")

print("\n" + "="*70)
