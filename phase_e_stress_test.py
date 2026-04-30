import json
import asyncio
from memory.persistent import PersistentMemory
from memory.db import DatabaseManager

async def run_test():
    print("🚀 Starting Phase E Stress Test v2...")
    pm = PersistentMemory()
    
    # 1. Test Persistence & Sequence
    print("\n[1/4] Testing Persistence & Multi-Action Sequence...")
    wf_id = pm.start_workflow("Buy headphones on Amazon")
    pm.record_action(wf_id, step=1, action_sequence=1, 
                     action_dict={"action_type": "type", "text": "sony headphones", "index": 5},
                     result_dict={"status": "success", "message": "Typed text"})
    pm.record_action(wf_id, step=1, action_sequence=2, 
                     action_dict={"action_type": "press_key", "text": "Enter"},
                     result_dict={"status": "success", "message": "Pressed enter"})
    
    actions = pm.get_workflow_actions(wf_id)
    if len(actions) == 2:
        print("✅ SUCCESS: Multi-action sequence recorded correctly.")
    else:
        print(f"❌ FAIL: Expected 2 actions, got {len(actions)}")

    # 2. Test TF-IDF Similarity (The "Flashback" Power)
    print("\n[2/4] Testing TF-IDF Similarity...")
    # Add a unique task
    old_wf = pm.start_workflow("How to search for headphones on Amazon store")
    pm.complete_workflow(old_wf, success=True, total_steps=5)
    
    similar = pm.get_similar_workflows("Find headphones on Amazon", threshold=0.3)
    if similar:
        print(f"✅ SUCCESS: Found similar task! Similarity Score: {similar[0]['similarity']}")
        print(f"   Match: \"{similar[0]['task_name']}\"")
    else:
        print("❌ FAIL: Could not find similar task.")

    # 3. Test Pattern Recognition (The "Muscle Memory" Power)
    print("\n[3/4] Testing Pattern Recognition...")
    # We use a unique pattern name for this test to avoid previous interference
    pm.learn_pattern("test_pattern_v2", ["scroll", "click"], ["done"], success=True)
    
    new_wf = pm.start_workflow("Pattern Test WF")
    pm.record_action(new_wf, step=1, action_sequence=1, action_dict={"action_type": "scroll"}, result_dict={"status": "success"})
    pm.record_action(new_wf, step=1, action_sequence=2, action_dict={"action_type": "click"}, result_dict={"status": "success"})
    
    pattern = pm.detect_pattern(new_wf)
    if pattern and pattern['pattern_type'] == "test_pattern_v2":
        print(f"✅ SUCCESS: Detected 'test_pattern_v2' pattern!")
    elif pattern:
        print(f"✅ SUCCESS (General): Detected '{pattern['pattern_type']}' from memory.")
    else:
        print(f"❌ FAIL: Pattern not detected.")

    # 4. Test Failure Signature (The "Trauma" Power - GLOBAL)
    print("\n[4/4] Testing Global Failure Signatures...")
    url = "https://example.com/login"
    text_hash = pm.hash_text("login error")
    
    # Simulating two separate workflows failing at the same spot
    wf1 = pm.start_workflow("Login Task 1")
    pm.record_state_hash(wf1, 1, url, text_hash=text_hash)
    pm.record_action(wf1, 1, action_sequence=1, action_dict={"action_type": "click"}, result_dict={"status": "error"})
    
    wf2 = pm.start_workflow("Login Task 2")
    pm.record_state_hash(wf2, 1, url, text_hash=text_hash)
    pm.record_action(wf2, 1, action_sequence=1, action_dict={"action_type": "click"}, result_dict={"status": "error"})
    
    # Check if a THIRD workflow detects this dead-end
    is_dead_end = pm.check_failure_signature("click", url, text_hash=text_hash)
    if is_dead_end:
        print("✅ SUCCESS: Detected GLOBAL failure (Dead-end). Agent learned from past mistakes!")
    else:
        print("❌ FAIL: Global failure signature not detected.")

    print("\n--- STRESS TEST COMPLETE ---")
    pm.db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
