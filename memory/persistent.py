"""
Phase E: Persistent Memory Engine
Cross-session learning, pattern matching, blocker recall, and workflow history.
This is the brain's long-term memory — everything else plugs into it.
"""

import json
import hashlib
import logging
import math
from collections import Counter
from datetime import datetime

from .db import DatabaseManager

logger = logging.getLogger("papper-memory")


class PersistentMemory:
    """Cross-session learning engine backed by SQLite.
    
    Responsibilities:
        1. Record full workflows (task + actions + outcomes)
        2. Find similar past workflows (Jaccard similarity on task words)
        3. Detect action-sequence patterns (CBR: Case-Based Reasoning)
        4. Store & recall blocker bypass methods
        5. Track state hashes for loop / stuck detection
    """

    def __init__(self, db=None):
        self.db = db or DatabaseManager()

    # ==================================================================
    # 1. WORKFLOW RECORDING
    # ==================================================================

    def start_workflow(self, task_name):
        """Start a new workflow."""
        if not task_name or not isinstance(task_name, str):
            raise ValueError("task_name must be a non-empty string")
        """Begin tracking a new task run. Returns workflow_id."""
        cur = self.db.execute(
            "INSERT INTO workflows (task_name) VALUES (?)",
            (task_name,),
        )
        wf_id = cur.lastrowid

        # Keep FTS in sync (if available)
        try:
            self.db.execute(
                "INSERT INTO workflows_fts (rowid, task_name) VALUES (?, ?)",
                (wf_id, task_name),
            )
        except Exception:
            pass  # FTS5 not available — acceptable

        logger.info(f"Workflow #{wf_id} started: {task_name}")
        return wf_id

    def record_action(self, workflow_id, step, action_dict, result_dict,
                      action_sequence=1, thought=None, url=None, state_changed=False):
        """Persist a single action + result within a workflow."""
        self.db.execute(
            """INSERT INTO actions
               (workflow_id, step, action_sequence, action_type, action_params, 
                thought, result_status, result_msg, state_changed, url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                workflow_id,
                step,
                action_sequence,
                action_dict.get("action_type", "unknown"),
                json.dumps(action_dict),
                thought,
                result_dict.get("status", "unknown"),
                result_dict.get("message", ""),
                int(state_changed),
                url,
            ),
        )

    def complete_workflow(self, workflow_id, success, total_steps, notes=None):
        """Finalise a workflow with its outcome."""
        self.db.execute(
            """UPDATE workflows
               SET completed_at = datetime('now'),
                   success      = ?,
                   total_steps  = ?,
                   notes        = ?
               WHERE id = ?""",
            (int(success), total_steps, notes, workflow_id),
        )
        logger.info(
            f"Workflow #{workflow_id} completed — "
            f"{'SUCCESS' if success else 'FAILED'} in {total_steps} steps."
        )

    # ==================================================================
    # 2. SIMILAR WORKFLOW LOOKUP (TF-IDF + Cosine Similarity)
    # ==================================================================

    def get_similar_workflows(self, task_name, threshold=0.3, limit=5):
        """Find past workflows whose task name is similar.

        Uses TF-IDF weighted cosine similarity:
            1. Tokenize task names into words
            2. Compute IDF (Inverse Document Frequency) across all stored tasks
            3. Build TF-IDF vectors for each task
            4. Compare using cosine similarity

        This correctly down-weights common filler words ("search", "for", "on")
        and up-weights meaningful words ("SpaceX", "Amazon", "headphones").

        Returns list of dicts:
            [{workflow_id, task_name, success, total_steps, similarity}, ...]
        """
        target_tokens = task_name.lower().split()
        if not target_tokens:
            return []

        rows = self.db.fetchall(
            "SELECT id, task_name, success, total_steps FROM workflows"
        )
        if not rows:
            return []

        # Build document corpus: each task name is a "document"
        all_docs = [target_tokens]  # index 0 = the query
        row_list = []
        for row in rows:
            tokens = row["task_name"].lower().split()
            all_docs.append(tokens)
            row_list.append(row)

        # Compute IDF: log(total_docs / docs_containing_term)
        total_docs = len(all_docs)
        doc_freq = Counter()  # how many documents each word appears in
        for doc in all_docs:
            unique_words = set(doc)
            for word in unique_words:
                doc_freq[word] += 1

        idf = {}
        for word, freq in doc_freq.items():
            idf[word] = math.log(total_docs / freq) if freq > 0 else 0.0

        def tfidf_vector(tokens):
            """Build a TF-IDF vector (dict) for a token list."""
            tf = Counter(tokens)
            total = len(tokens) if tokens else 1
            return {word: (count / total) * idf.get(word, 0.0)
                    for word, count in tf.items()}

        def cosine_sim(vec_a, vec_b):
            """Cosine similarity between two sparse vectors (dicts)."""
            common_keys = set(vec_a.keys()) & set(vec_b.keys())
            if not common_keys:
                return 0.0
            dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
            mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
            mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)

        # Compute similarity for each stored workflow
        target_vec = tfidf_vector(target_tokens)
        scored = []
        for i, row in enumerate(row_list):
            row_vec = tfidf_vector(all_docs[i + 1])  # +1 because index 0 is the query
            sim = cosine_sim(target_vec, row_vec)
            if sim >= threshold:
                scored.append({
                    "workflow_id": row["id"],
                    "task_name": row["task_name"],
                    "success": bool(row["success"]),
                    "total_steps": row["total_steps"],
                    "similarity": round(sim, 3),
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    def get_workflow_actions(self, workflow_id):
        """Retrieve the full action sequence of a past workflow."""
        rows = self.db.fetchall(
            """SELECT step, action_type, action_params, thought,
                      result_status, result_msg, state_changed, url
               FROM actions WHERE workflow_id = ? ORDER BY step""",
            (workflow_id,),
        )
        return [dict(r) for r in rows]

    # ==================================================================
    # 3. PATTERN DETECTION (CBR — Case-Based Reasoning)
    # ==================================================================

    def detect_pattern(self, workflow_id, window=5):
        """Check if the recent action-types match a known pattern.

        Queries the database directly to get the sequence of recently 
        executed actions for this workflow.

        Returns:
            {pattern_type, success_rate, recommended_next} or None
        """
        rows = self.db.fetchall(
            """SELECT action_type FROM actions 
               WHERE workflow_id = ? 
               ORDER BY step DESC, action_sequence DESC 
               LIMIT ?""",
            (workflow_id, window),
        )
        if not rows:
            return None

        # Sequence should be in chronological order
        sequence = [r["action_type"] for r in rows]
        sequence.reverse()

        rows = self.db.fetchall(
            "SELECT * FROM patterns ORDER BY success_count DESC"
        )

        for row in rows:
            rule = json.loads(row["detection_rule"])  # list of action_types
            rule_len = len(rule)

            # Exact tail match: sequence must end with the full rule
            if rule_len <= len(sequence) and sequence[-rule_len:] == rule:
                total = row["success_count"] + row["fail_count"]
                rate = row["success_count"] / total if total > 0 else 0.0
                response = json.loads(row["response_action"])
                # Touch last_used_at
                self.db.execute(
                    "UPDATE patterns SET last_used_at = datetime('now') WHERE id = ?",
                    (row["id"],),
                )
                return {
                    "pattern_type": row["pattern_type"],
                    "success_rate": round(rate, 3),
                    "recommended_next": response,
                }
        return None

    def learn_pattern(self, pattern_type, action_sequence, recommended_next, success=True):
        """Register or update a learned action pattern.

        If a pattern with the same detection_rule exists, increment counts.
        Otherwise create a new one.
        """
        detection_rule = json.dumps(
            [a.get("action_type", a) if isinstance(a, dict) else a
             for a in action_sequence]
        )
        response_action = json.dumps(recommended_next)

        existing = self.db.fetchone(
            "SELECT id, success_count, fail_count FROM patterns WHERE detection_rule = ?",
            (detection_rule,),
        )

        if existing:
            col = "success_count" if success else "fail_count"
            self.db.execute(
                f"UPDATE patterns SET {col} = {col} + 1, last_used_at = datetime('now') WHERE id = ?",
                (existing["id"],),
            )
        else:
            self.db.execute(
                """INSERT INTO patterns
                   (pattern_type, detection_rule, response_action,
                    success_count, fail_count, last_used_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (
                    pattern_type,
                    detection_rule,
                    response_action,
                    1 if success else 0,
                    0 if success else 1,
                ),
            )
        logger.info(f"Pattern learned: {pattern_type} ({'✓' if success else '✗'})")

    # ==================================================================
    # 4. BLOCKER MANAGEMENT
    # ==================================================================

    def learn_blocker(self, blocker_type, url_pattern, detection_rule, bypass_method):
        """Register a new blocker or update an existing one.

        blocker_type: modal | paywall | captcha | rate_limit
        """
        existing = self.db.fetchone(
            "SELECT id FROM blockers WHERE blocker_type = ? AND url_pattern = ?",
            (blocker_type, url_pattern),
        )

        if existing:
            self.db.execute(
                """UPDATE blockers
                   SET detection_rule = ?, bypass_method = ?,
                       last_seen_at = datetime('now')
                   WHERE id = ?""",
                (json.dumps(detection_rule), json.dumps(bypass_method), existing["id"]),
            )
        else:
            self.db.execute(
                """INSERT INTO blockers
                   (blocker_type, url_pattern, detection_rule, bypass_method)
                   VALUES (?, ?, ?, ?)""",
                (
                    blocker_type,
                    url_pattern,
                    json.dumps(detection_rule),
                    json.dumps(bypass_method),
                ),
            )
        logger.info(f"Blocker recorded: {blocker_type} @ {url_pattern}")

    def get_blocker_bypass(self, blocker_type, url=None):
        """Retrieve a known bypass for a blocker type.

        Optionally filter by URL pattern.
        Returns bypass_method dict or None.
        """
        if url:
            row = self.db.fetchone(
                """SELECT bypass_method FROM blockers
                   WHERE blocker_type = ? AND ? LIKE '%' || url_pattern || '%'
                   ORDER BY success_count DESC LIMIT 1""",
                (blocker_type, url),
            )
        else:
            row = self.db.fetchone(
                """SELECT bypass_method FROM blockers
                   WHERE blocker_type = ?
                   ORDER BY success_count DESC LIMIT 1""",
                (blocker_type,),
            )

        if row:
            return json.loads(row["bypass_method"])
        return None

    def record_blocker_outcome(self, blocker_type, url_pattern, success):
        """Increment success/fail counter for a blocker bypass."""
        col = "success_count" if success else "fail_count"
        self.db.execute(
            f"""UPDATE blockers SET {col} = {col} + 1,
                last_seen_at = datetime('now')
                WHERE blocker_type = ? AND url_pattern = ?""",
            (blocker_type, url_pattern),
        )

    # ==================================================================
    # 5. STATE HASH TRACKING (for loop & stuck detection)
    # ==================================================================

    def record_state_hash(self, workflow_id, step, url,
                          visual_hash=None, text_hash=None):
        """Save a state snapshot for the current step."""
        if not visual_hash or not text_hash:
            raise ValueError("Both visual_hash and text_hash must be provided (not None or empty)")
        if step < 1:
            raise ValueError(f"step must be >= 1, got {step}")

        self.db.execute(
            """INSERT INTO state_hashes
               (workflow_id, step, visual_hash, text_hash, url)
               VALUES (?, ?, ?, ?, ?)""",
            (workflow_id, step, visual_hash, text_hash, url),
        )

    def is_state_repeated(self, workflow_id, visual_hash=None, text_hash=None, lookback=5):
        """Check if the current state matches any of the last N states.

        This is the core loop-detection mechanism from the research:
            If StateHash_current == StateHash_previous → likely in a loop.

        IMPORTANT: Both visual_hash AND text_hash must match for true loop detection.
        Partial matches (only visual OR only text) indicate progress, not loops.

        Returns:
            (is_repeated, repeat_count)
        """
        # Must have both hashes for meaningful loop detection
        if not (visual_hash and text_hash):
            raise ValueError("Both visual_hash and text_hash required for loop detection (not None or empty)")

        # First select the last lookback state IDs, then count matches within that subset.
        # (Using COUNT(*) directly with LIMIT doesn't work as intended; it counts all matches, not limited set)
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

        count = rows[0]["cnt"] if rows else 0
        return count >= 2, count

    def get_last_known_state(self, url):
        """Retrieve the most recent state hash recorded at a given URL.

        Used for resuming interrupted tasks.
        """
        row = self.db.fetchone(
            """SELECT workflow_id, step, visual_hash, text_hash
               FROM state_hashes WHERE url = ?
               ORDER BY id DESC LIMIT 1""",
            (url,),
        )
        return dict(row) if row else None

    # ==================================================================
    # 6. FAILURE SIGNATURE (from AutoGPT research)
    # ==================================================================

    def check_failure_signature(self, workflow_id, action_type, url, text_hash=None):
        """Check if this exact (action + state) combo has failed before.

        Failure Signature = StateHash + Action → repeated error.
        If it failed 2+ times at the same state, it's a known dead-end.

        Returns True if this is a known dead-end.
        """
        if text_hash:
            rows = self.db.fetchall(
                """SELECT a.id FROM actions a
                   JOIN state_hashes s ON a.workflow_id = s.workflow_id AND a.step = s.step
                   WHERE a.workflow_id = ?
                     AND a.action_type = ?
                     AND a.result_status = 'error'
                     AND s.url = ?
                     AND s.text_hash = ?""",
                (workflow_id, action_type, url, text_hash),
            )
        else:
            rows = self.db.fetchall(
                """SELECT a.id FROM actions a
                   JOIN state_hashes s ON a.workflow_id = s.workflow_id AND a.step = s.step
                   WHERE a.workflow_id = ?
                     AND a.action_type = ?
                     AND a.result_status = 'error'
                     AND s.url = ?""",
                (workflow_id, action_type, url),
            )
        return len(rows) >= 2

    # ==================================================================
    # UTILITY: Hashing helpers
    # ==================================================================

    @staticmethod
    def hash_text(text):
        """SHA-256 of normalized text (for grid content)."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def hash_visual(screenshot_bytes):
        """MD5 of raw screenshot bytes (fast, not crypto-secure — fine for comparison)."""
        return hashlib.md5(screenshot_bytes).hexdigest()

    # ==================================================================
    # CBR RETRIEVAL: Build few-shot context for the LLM
    # ==================================================================

    def get_cbr_context(self, task_name, max_cases=3):
        """Case-Based Reasoning retrieval for LLM prompt injection.

        Find similar past workflows, grab their successful action sequences,
        and format them as few-shot examples.

        Returns a string ready to append to the planner prompt.
        """
        similar = self.get_similar_workflows(task_name, threshold=0.3, limit=max_cases)
        if not similar:
            return ""

        context_lines = ["--- PAST EXPERIENCE (similar tasks) ---"]
        for wf in similar:
            if not wf["success"]:
                continue  # Only inject successful cases

            actions = self.get_workflow_actions(wf["workflow_id"])
            if not actions:
                continue

            context_lines.append(
                f"\nTask: \"{wf['task_name']}\" (similarity: {wf['similarity']}, "
                f"steps: {wf['total_steps']})"
            )
            for a in actions[:8]:  # Cap at 8 steps to save tokens
                status_icon = "✓" if a["result_status"] == "success" else "✗"
                context_lines.append(
                    f"  Step {a['step']}: {a['action_type']} → {status_icon} {a['result_msg']}"
                )

        if len(context_lines) <= 1:
            return ""  # No successful cases found

        return "\n".join(context_lines)

    # ==================================================================
    # STATS
    # ==================================================================

    def get_stats(self):
        """Quick overview of the memory database."""
        wf = self.db.fetchone("SELECT COUNT(*) as c FROM workflows")
        ac = self.db.fetchone("SELECT COUNT(*) as c FROM actions")
        pt = self.db.fetchone("SELECT COUNT(*) as c FROM patterns")
        bl = self.db.fetchone("SELECT COUNT(*) as c FROM blockers")
        sr = self.db.fetchone(
            "SELECT ROUND(AVG(success)*100, 1) as rate FROM workflows WHERE completed_at IS NOT NULL"
        )
        return {
            "workflows": wf["c"],
            "actions": ac["c"],
            "patterns": pt["c"],
            "blockers": bl["c"],
            "success_rate": sr["rate"] or 0.0,
        }

    # ==================================================================
    # 7. PHASE F: Cross-Workflow & Recovery Helpers
    # ==================================================================

    def check_cross_workflow_failure_signature(
        self, action_type, url, text_hash=None, threshold=3
    ):
        """Check if this action+state combo failed across ALL past workflows.

        Unlike check_failure_signature (which checks within ONE workflow),
        this looks across the entire history. If clicking at amazon.com
        failed 3+ times across 3 different tasks, something is structurally
        wrong with that action at that URL — avoid it entirely.

        Returns True if this is a known cross-workflow dead-end.
        """
        params = [action_type, "error"]
        text_clause = ""

        if text_hash:
            text_clause = "AND sh.text_hash = ?"
            params.append(text_hash)

        # Use domain matching (LIKE '%url%') so amazon.com/phones and
        # amazon.com/laptops both match a check for "amazon.com"
        params.append(f"%{url}%")

        rows = self.db.fetchall(
            f"""SELECT COUNT(DISTINCT a.workflow_id) as cnt FROM actions a
                JOIN state_hashes sh ON a.workflow_id = sh.workflow_id AND a.step = sh.step
                WHERE a.action_type = ? AND a.result_status = ?
                {text_clause}
                AND sh.url LIKE ?""",
            params,
        )
        count = rows[0]["cnt"] if rows else 0
        if count >= threshold:
            logger.warning(
                f"Cross-workflow failure: {action_type} at {url} "
                f"failed in {count} workflows (threshold={threshold})"
            )
        return count >= threshold

    def get_recent_actions_with_states(self, workflow_id, limit=5):
        """Get recent actions joined with their state info.

        Used by LoopResolver to build a summary of "what the agent has been
        doing and what happened to the page each time."

        Returns list of dicts with action + state columns.
        """
        rows = self.db.fetchall(
            """SELECT a.step, a.action_type, a.result_status, a.state_changed,
                      sh.url, sh.visual_hash, sh.text_hash
               FROM actions a
               LEFT JOIN state_hashes sh
                   ON a.workflow_id = sh.workflow_id AND a.step = sh.step
               WHERE a.workflow_id = ?
               ORDER BY a.step DESC, a.action_sequence DESC
               LIMIT ?""",
            (workflow_id, limit),
        )
        return [dict(r) for r in rows]

    def record_finding(self, workflow_id, key, value, step):
        """Record a semantic finding (Phase H TaskMemory integration point).

        Phase F doesn't use this yet, but Phase H will store structured
        findings like "price = $299" or "title = iPhone 15 Pro" that the
        agent discovers during execution.
        """
        pass  # Stub — no-op until Phase H
