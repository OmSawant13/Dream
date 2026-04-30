# Phase E: Persistent Memory & Cognitive Retrieval (Level 3)

## Objective
Transition the Papper Agent from an ephemeral "one-off" executor to a learning system that persists workflows, detects loops via UI signatures, and utilizes Case-Based Reasoning (CBR) to improve success rates over time.

---

## 1. Architectural Core: SQLite Persistence
We will use SQLite with the **FTS5 extension** for high-performance lexical retrieval and standard relational tables for structured workflow tracking.

### Database Schema
```sql
-- Main Workflow tracking
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    task_description TEXT,
    status TEXT, -- 'success', 'failed', 'running'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual steps within a workflow
CREATE TABLE workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT,
    state_signature TEXT, -- SHA256 hash of interactive UI elements
    action_type TEXT,
    action_description TEXT,
    thought TEXT,
    outcome TEXT,
    FOREIGN KEY(workflow_id) REFERENCES workflows(id)
);

-- Persistent Blockers (To prevent infinite loops across sessions)
CREATE TABLE blockers (
    state_signature TEXT,
    blocked_action TEXT,
    reason TEXT,
    PRIMARY KEY (state_signature, blocked_action)
);
```

---

## 2. Loop Resilience: Structural Hashing
Instead of simple URL-based detection, we implement **Structural UI Signatures**.
- **Algorithm**: 
  1. Extract all interactive elements (buttons, inputs, links).
  2. Map them to a stable string: `tag:attr[name]:text`.
  3. Hash the resulting list.
- **Benefit**: If a popup opens but the URL stays the same, the hash changes. If we are stuck on a loading spinner, the hash stays the same.

---

## 3. Case-Based Reasoning (CBR) Cycle
We implement the 4R cycle inspired by MemGPT and AutoGPT:

1. **Retrieve**: 
   - When a new task starts, query SQLite using **Hybrid Scoring**:
     - `Lexical Score`: FTS5 match on `task_description`.
     - `Structural Score`: Jaccard similarity on `state_signature`.
   - Result: Top 3 most relevant past workflows.

2. **Reuse**:
   - Inject these "Cases" into the `PlanningEngine` as Few-Shot examples.
   - *Prompt Injection*: "Past similar task: [Description]. Step 1 was [Action]. Result: [Success]."

3. **Revise**:
   - If the agent proposes an action that is in the `blockers` table for the current `state_signature`, the `AgentLoop` rejects it and forces the Planner to re-think.

4. **Retain**:
   - On task completion (Success/Failure), the entire trace is committed to the DB.

---

## 4. Implementation Roadmap
1. **Module 1**: `memory/persistent.py` - SQLite wrapper with FTS5 and Hybrid Retrieval logic.
2. **Module 2**: `browser/observer.py` - Update to include `get_state_signature()` using SHA256.
3. **Module 3**: `agent/agent.py` - Update the loop to check for blockers and save steps.
4. **Module 4**: `planner/engine.py` - Update prompt construction to include "Retrieved Memory" context.

---

## 5. Industry Benchmarking (Verified Patterns)
| Feature | BabyAGI | AutoGPT | MemGPT | Papper Agent (Phase E) |
| :--- | :--- | :--- | :--- | :--- |
| **Storage** | Deque / Vector | Multi-Backend | SQLite/Postgres | SQLite + FTS5 |
| **Retrieval** | Embeddings | Embedding Search | Tool-based Query | Hybrid (FTS5 + Jaccard) |
| **Loop Control** | LLM Re-rank | Cycle Budget | Event Buffer | **Structural UI Hashing** |
| **Persistence** | Ephemeral | Configurable | Persistent | **Strictly Persistent** |
