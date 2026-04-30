# LEVEL 3 — COMPLETE INTELLIGENT BROWSER AGENT
## Comprehensive Implementation Plan (Phases E-J)

**Status:** Research-backed architecture. Production-ready design. Ready for implementation after user approval.

---

## CONTEXT: Why Level 3?

**Level 2 is TEMPORARY.** It works for simple tasks (Google search, YouTube navigation) but FAILS on:
1. **State Uncertainty** — Agent doesn't know if action succeeded (YouTube stuck at "need to play video")
2. **Dynamic Content** — Page loading not detected in grid (GitHub search didn't render)
3. **Content Parsing** — Can't extract prices/ratings intelligently (regex brittle)
4. **Error Recovery** — Modals/paywalls block progress permanently
5. **Learning** — Repeats mistakes every run, no pattern recognition
6. **Multi-Step Workflows** — Can't book flights, compare products (requires parallel tabs)
7. **Data Export** — No structured output (JSON/CSV)
8. **Rate Limiting** — Gets throttled, no backoff strategy

**Level 3 solves ALL of these.** Once built, it's PRODUCTION-GRADE.

---

## PHASE ROADMAP

```
FOUNDATION
    ↓
Phase E: Persistent Memory (Week 1)
    ├─ SQLite workflow storage
    ├─ Pattern matching engine
    ├─ Cross-run learning
    └─ Feeds everything else

STATE INTELLIGENCE
    ↓
Phase F: State Verification (Week 2)
    ├─ Visual hash (screenshot)
    ├─ Text hash (grid content)
    ├─ Dual verification
    └─ Feeds Phase G decisions

CONTENT INTELLIGENCE
    ↓
Phase G: Content Understanding (Week 2-3)
    ├─ LLM-based extraction
    ├─ Unit awareness (currency, ratings, dates)
    ├─ Semantic parsing
    └─ Feeds Phase J export

EXECUTION INTELLIGENCE
    ├─ Phase H: Multi-Tab Orchestration (Week 3-4)
    │   ├─ Parallel browser contexts
    │   ├─ Workflow splitting
    │   └─ Feeds Phase I recovery
    │
    └─ Phase I: Advanced Error Recovery (Week 4)
        ├─ Modal/paywall detection
        ├─ Exponential backoff
        ├─ CAPTCHA indicators
        └─ Feeds Phase E learning

DATA EXTRACTION
    ↓
Phase J: Structured Data Export (Week 4-5)
    ├─ JSON schema generation
    ├─ CSV/Table export
    ├─ API endpoint
    └─ Uses Phase G + Phase E
```

---

## DETAILED PHASE BREAKDOWN

### **PHASE E: PERSISTENT MEMORY** (Week 1)
**Why this first:** Everything else depends on it. No other phase works without E.

#### **Problem E Solves**
- Level 2: Agent repeats same mistake on YouTube, GitHub tasks every run
- Agent: Has no memory of failures, patterns, or learned optimizations
- Symptom: If task A fails with modal at step 3, next day still fails same way

#### **Architecture**

```sql
-- SQLite Database Schema

TABLE workflows
  id (PK), task_name, created_at, completed_at, success (bool)
  
TABLE actions (action history across runs)
  id (PK), workflow_id (FK), step, action_type, action_params, 
  result_status, state_changed (bool), timestamp
  
TABLE patterns (learned behaviors)
  id (PK), pattern_type, detection_rule (JSON), 
  response_action (JSON), success_rate, last_used_at
  
TABLE blockers (known obstacles)
  id (PK), blocker_type (modal/paywall/captcha), 
  detection_selector, bypass_method, last_seen_at
  
TABLE state_hashes (for quick comparison)
  id (PK), workflow_id (FK), step, visual_hash, 
  text_hash, url, timestamp
```

#### **Module: `memory/persistent.py`**

```python
class PersistentMemory:
    """Cross-session learning engine."""
    
    def __init__(self, db_path="papper.db"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def record_workflow(self, task_name, actions, success):
        """Save entire workflow to database."""
        # Stores task, all actions, state hashes, results
        
    def get_similar_workflows(self, task_name, threshold=0.8):
        """
        Find past similar tasks using Jaccard Similarity on tokenized task words.
        Logic: Intersection(words1, words2) / Union(words1, words2)
        """
        # Returns: [past_workflow, success_rate]
        
    def detect_pattern(self, last_5_actions):
        """Identify if action sequence matches known pattern."""
        # If "click search, wait, scroll, read results" = search pattern
        # Returns: (pattern_name, success_rate, recommended_next_action)
        
    def learn_blocker(self, blocker_type, detection_rule, bypass_method):
        """Register a modal/paywall and how to handle it."""
        # Next time we see this modal → auto-handle it
        
    def get_state_recovery(self, url):
        """Get previous state at similar URL."""
        # For resuming interrupted tasks
```

#### **Why This Approach**
- **SQLite:** No external dependencies, works offline, fast queries
- **Simple Similarity:** Jaccard Similarity (Intersection over Union) for fast, zero-ML task matching
- **Patterns:** Learn from 3+ similar tasks → predict next step
- **Blockers:** Build a blockers library (modals, paywalls, CAPTCHAs)
- **State recovery:** If interrupted, resume from last known good state

#### **Success Metric**
- Agent completes same task FASTER on 2nd run
- Agent recognizes modal patterns without explicit instruction
- 80%+ pattern match accuracy on similar tasks

---

### **PHASE F: STATE VERIFICATION** (Week 2)
**Why after E:** Needs E's database to log state changes and learn patterns.

#### **Problem F Solves**
- Level 2: YouTube task — agent navigated to video but didn't know video was playing
- Level 2: GitHub task — search didn't render, agent didn't detect it
- Symptom: Agent thinks action failed when it succeeded (or vice versa)

#### **Your Enhancement: Visual + Text Hashing**

```python
class StateVerifier:
    """Detect if actions actually changed page state."""
    
    async def verify_action(self, action, screenshot_before, screenshot_after, 
                           grid_before, grid_after):
        """Returns: (state_changed, change_type, confidence)"""
        
        # Visual hash: MD5 of screenshot bytes
        visual_hash_before = md5(screenshot_before)
        visual_hash_after = md5(screenshot_after)
        visual_changed = visual_hash_before != visual_hash_after
        
        # Text hash: SHA256 of normalized grid
        text_hash_before = sha256(grid_before.normalized())
        text_hash_after = sha256(grid_after.normalized())
        text_changed = text_hash_before != text_hash_after
        
        # Dual verification (either one = success, not both required)
        if visual_changed and text_changed:
            return True, "VISUAL_AND_TEXT", 1.0  # high confidence
        elif visual_changed:
            return True, "VISUAL_ONLY", 0.8  # moderate (UI responded, content loading)
        elif text_changed:
            return True, "TEXT_ONLY", 0.9  # good (content updated)
        else:
            return False, "NO_CHANGE", 0.0
```

#### **Integration with E**
- Every state change is logged to `state_hashes` table
- Enables pattern learning: "If we click search, visual changes in <500ms, then text in <2000ms"
- Agent learns which actions are slow vs fast

#### **Handles Level 2 Failures**
```
YouTube: click play button
  → visual_changed = True (player UI)
  → text_changed = False (title already loaded)
  → VISUAL_ONLY detected
  → Agent knows: "progress made, wait for content"

GitHub: click search
  → visual_changed = False (no spinner shown?)
  → text_changed = False (search results not rendered)
  → NO_CHANGE detected
  → Agent: "page didn't respond, retry with backoff"
```

#### **Success Metric**
- Detects 95%+ of actual state changes
- False positives <5% (incorrectly thinks something changed)
- Stuck detection reduced by 70% (no more "action succeeded but agent didn't know")

---

### **PHASE G: CONTENT UNDERSTANDING** (Week 2-3)
**Why after F:** Uses state verification to know when content is ready to parse.

#### **Problem G Solves**
- Level 2: Can't extract prices, ratings, flight prices (regex breaks)
- Symptom: Agent sees price but can't tell if it's "$99.99" or "RS 5000" or "on sale from $150"
- Real use case: Book flight → need to understand prices in any currency/format

#### **Your Enhancement: Small LLM Extraction**

```python
class ContentExtractor:
    """Parse unstructured web content using LLM."""
    
    async def extract_prices(self, grid_text, context=""):
        """Given grid output, find all prices intelligently."""
        prompt = f"""
        Grid content:
        {grid_text}
        
        Context: {context}
        
        Find ALL prices in this grid. For each, return JSON:
        [
          {"value": 99.99, "currency": "USD", "type": "current"},
          {"value": 150, "currency": "USD", "type": "original_crossed_out"},
          ...
        ]
        """
        # Uses Claude 3 Haiku or GPT-3.5 (cheap models)
        response = await llm.extract_json(prompt)
        return response
    
    async def extract_ratings(self, grid_text):
        """Parse ratings in any format (stars, numbers, emojis)."""
        # Handles: "5 stars", "5.0★", "⭐⭐⭐⭐⭐", "4/5"
        # Returns: {"value": 5.0, "scale": 5.0, "type": "star"}
    
    async def extract_dates(self, grid_text):
        """Parse dates in any format."""
        # Handles: "Apr 29, 2026", "29/04/2026", "2026-04-29"
        # Returns: ISO datetime
    
    async def extract_links(self, grid_text):
        """Find actionable links with context."""
        # "Click here to buy" → extract_links → {"text": "Click here to buy", "likely_target": "checkout"}
```

#### **Why Small LLM (not big model)**
- Cost: Haiku = 0.80 per 1M tokens (cheap)
- Speed: <500ms per extraction
- Reliability: Better than regex on edge cases
- Composable: Chain multiple extractors

#### **Integration with E + F**
- Phase E learns: "Flight prices always come in currency-value pairs"
- Phase F detects: "Grid changed, content ready for extraction"
- Agent chains: Observe → Verify → Extract → Decide

#### **Handles Level 2 Failures**
```
Task: Find cheapest flight

Grid shows:
[15] A: "Delhi → Mumbai: $199 | $250"
[16] A: "Bangalore → Mumbai: ₹5500 | ₹7200"

Regex extraction: BREAKS (different currencies, units)

LLM extraction:
  [
    {"route": "Delhi-Mumbai", "price": 199, "currency": "USD", "original": 250},
    {"route": "Bangalore-Mumbai", "price": 5500, "currency": "INR", "original": 7200}
  ]
  
Agent: "USD is cheaper, click first option"
```

#### **Success Metric**
- Extracts prices with 95%+ accuracy across formats
- Handles 10+ different date formats
- Works in 5+ languages
- <500ms per extraction

---

### **PHASE H: MULTI-TAB ORCHESTRATION** (Week 3-4)
**Why here:** Needs E (patterns) + F (state) + G (content) ready first.

#### **Problem H Solves**
- Level 2: Single browser tab = linear workflow only
- Can't compare flight prices (need tabs open simultaneously)
- Can't parallel-search multiple cities
- Symptom: Complex tasks timeout waiting for sequential operations

#### **Architecture**

```python
class MultiTabOrchestrator:
    """Manage multiple browser contexts for parallel workflows."""
    
    def __init__(self, max_tabs=3):
        self.tabs = {}  # tab_id → BrowserContext
        self.workflows = {}  # workflow_id → {tab_id, task, state}
    
    async def split_task(self, task):
        """Decompose complex task into parallel subtasks."""
        # "Find cheapest flight from Delhi, Mumbai, Bangalore to Singapore"
        # → 3 subtasks (one per city), open 3 tabs
        
        subtasks = await self.planner.decompose(task)
        # Returns: [
        #   {"tab": 1, "task": "Delhi → Singapore"},
        #   {"tab": 2, "task": "Mumbai → Singapore"},
        #   {"tab": 3, "task": "Bangalore → Singapore"}
        # ]
        
        return subtasks
    
    async def orchestrate(self, task):
        """Run parallel workflows, sync results."""
        subtasks = await self.split_task(task)
        
        # Launch all subtasks in parallel
        results = await asyncio.gather(*[
            self.run_subtask(st) for st in subtasks
        ])
        
        # Merge results (Phase G extracts prices from each tab)
        merged = self.merge_results(results)
        return merged
```

#### **Workflow Splitting Logic**
- Geographic tasks: Parallel searches in different locations
- Comparison tasks: Multiple products in parallel tabs
- Sequential gates: Wait for result from Tab 1, use in Tab 2

#### **Integration with E**
- Phase E knows: "For 'find cheapest flight' tasks, always split by origin city"
- Agent learns optimal parallelization strategy
- Caches decomposition patterns

#### **Success Metric**
- 3-tab parallel execution <3x slower than single tab
- Correctly merges results from 3+ tabs
- Doesn't lose context between tab switches
- Handles 100+ element grids across tabs

---

### **PHASE I: ADVANCED ERROR RECOVERY** (Week 4)
**Why here:** Needs H (orchestration context) + E (blocker learning).

#### **Problem I Solves**
- Level 2: Modals block progress, closing once fails, no retry
- Level 2: No handling of paywalls, CAPTCHAs, rate limits
- Symptom: One modal = entire task fails permanently

#### **Your Enhancement: Exponential Backoff + Retry Limits**

```python
class ErrorRecoveryEngine:
    """Detect blockers and recover intelligently."""
    
    async def handle_action_failure(self, action, error, attempt=1):
        """Retry with exponential backoff."""
        
        # Detect blocker type
        blocker_type = self.detect_blocker(error)  # modal, paywall, captcha, rate_limit
        
        if blocker_type == "modal":
            # Try to close modal (from Phase E blocker library)
            close_action = await self.memory.get_blocker_bypass(blocker_type)
            if close_action:
                await agent.execute_action(close_action)
                
                # Exponential backoff before retry
                wait_time = min(2 ** (attempt - 1), 16)  # 1s, 2s, 4s, 8s, 16s max
                await asyncio.sleep(wait_time)
                
                # Retry original action
                if attempt < 3:
                    return await self.handle_action_failure(action, error, attempt + 1)
        
        elif blocker_type == "rate_limit":
            # Wait 60s before retrying (from server backoff hint)
            await asyncio.sleep(60)
            if attempt < 2:
                return await self.handle_action_failure(action, error, attempt + 1)
        
        elif blocker_type == "captcha":
            # Mark task as blocked, await human intervention or skip
            logger.error(f"CAPTCHA detected. Task blocked.")
            return False
        
        return False
    
    def detect_blocker(self, error):
        """Identify what's blocking progress."""
        # Regex: "Please solve the CAPTCHA" → captcha
        # Regex: "Too many requests" → rate_limit
        # Visual: Modal overlay detected → modal
        # HTTP 429 → rate_limit
        # HTTP 402 → paywall
```

#### **Backoff Strategy Details**
```
Attempt 1: Immediate retry
  ↓ fails
Attempt 2: Wait 2s, retry
  ↓ fails
Attempt 3: Wait 4s, retry
  ↓ fails
Give up: Log to Phase E, record blocker pattern
```

#### **Integration with E**
- Phase E stores: "At pinterest.com, close button has selector '.close-icon'"
- Next time: Auto-close without retrying
- Learns: "Modal closing takes 2-3s, wait accordingly"

#### **Handles Level 2 Failures**
```
GitHub: Search modal appears
  1st close: Still loading
  Wait 2s
  2nd close: Actually closes
  Search results render
  ✓ SUCCESS
  
vs Level 2: Close once, fails immediately
```

#### **Success Metric**
- 70%+ recovery rate on fixable errors
- CAPTCHA detection <100ms
- Modal close rate >95%
- No infinite retry loops (max 3 attempts)

---

### **PHASE J: STRUCTURED DATA EXTRACTION** (Week 4-5)
**Why last:** Uses everything (E, F, G, H, I) to extract final results.

#### **Problem J Solves**
- Level 2: Agent finds information but can't export it
- Symptom: User asks "get top 5 HackerNews stories" → Agent reads them but no output format
- Real use: Need JSON/CSV for downstream systems

#### **Architecture**

```python
class DataExtractor:
    """Export structured data from browsing sessions."""
    
    async def extract_as_json(self, task, extraction_schema):
        """Given schema, extract matching data from all visited pages."""
        # Schema:
        # {
        #   "stories": [
        #     {"title": "string", "points": "number", "author": "string"}
        #   ]
        # }
        
        # Phase G extracts text per page
        # Phase J validates against schema
        # Returns: {stories: [{title, points, author}, ...]}
    
    async def extract_as_csv(self, task, columns):
        """Export as CSV with headers."""
        # columns: ["story_title", "points", "author"]
        # Returns: CSV bytes
    
    async def create_api_endpoint(self, task_id):
        """Expose results as REST API."""
        # GET /api/results/{task_id}
        # Returns: JSON result
```

#### **Integration with Phase G**
```
Phase G extracts: {"title": "...", "points": 100, "author": "..."}
Phase J validates: Does it match schema?
Phase J exports: JSON or CSV
```

#### **Example Flow**
```
Task: "Get top 5 HackerNews stories"

Agent runs (H orchestrates, F verifies, G extracts):
  Page 1: [story1, story2, story3]
  Page 2: [story4, story5]

Phase J validation:
  ✓ story1: {title, points, author} → VALID
  ✓ story2: {title, points, author} → VALID
  ...
  ✗ story6: missing 'author' → SKIP

Export:
  JSON: {"stories": [5 valid stories]}
  CSV: title,points,author\n...
  API: GET /results/task123 → JSON
```

#### **Success Metric**
- 90%+ schema validation success
- Exports match manual inspection
- <100ms to generate JSON/CSV
- API endpoint available within 1s of completion

---

## CROSS-PHASE INTEGRATION

### **Data Flow: Complete Task**

```
User: "Find 3 cheapest flights Delhi→Singapore, export as JSON"

Phase H: Decompose
  → 1 search task (Delhi→Singapore flights)
  
Phase E: Pattern recall
  → "Flight search task: click search, wait 3s, scroll, extract prices"
  
Phase F: State verification
  → Click search
  → Visual changed (search UI active)
  → Text changed (results loaded)
  → ✓ Proceed
  
Phase G: Content extraction
  → LLM extracts all prices from grid
  → Returns: [{price: 199, airline: "AI"}, {price: 210, airline: "AA"}, ...]
  
Phase I: Recovery
  → (No errors encountered)
  
Phase J: Data export
  → Validates prices against schema
  → Exports as JSON: {flights: [{price, airline, date}]}
  
Return: JSON to user
```

### **Error Recovery Flow**

```
Phase F: Click button → NO_CHANGE detected
  ↓
Phase I: Detect modal
  ↓ Fetch bypass method from Phase E
  ↓ Close modal
  ↓ Wait 2s (backoff)
  ↓ Retry original action
  ↓ If success: Continue
  ↓ If fail: Log to Phase E, mark blocker
```

---

## IMPLEMENTATION TIMELINE

| Phase | Duration | Start | Key Deliverables | Dependencies |
|-------|----------|-------|-------------------|--------------|
| **E** | 1 week | Week 1 | SQLite schema, PersistentMemory class, pattern matching | None |
| **F** | 1 week | Week 2 | StateVerifier (visual+text), state logging to E | E |
| **G** | 1.5 weeks | Week 2 | LLM extraction (prices, dates, links), Schema validation | E, F |
| **H** | 1.5 weeks | Week 3 | TaskDecomposer, MultiTabOrchestrator, result merging | E, F, G |
| **I** | 1 week | Week 4 | ErrorRecoveryEngine, blocker detection, backoff logic | E, H |
| **J** | 1 week | Week 4 | DataExtractor (JSON/CSV), Schema validation, API endpoint | E, G |

**Total: 6.5 weeks to production-ready Level 3**

**Parallel opportunities:**
- Weeks 3-4: Start H while finishing G
- Weeks 4-5: Start J while finishing I
- **Total effective: 5.5 weeks with parallel work**

---

## SUCCESS CRITERIA: WHEN IS LEVEL 3 "READY"?

### **Functional Requirements**
- ✓ Complete simple tasks (search, navigate, read) with 95%+ success
- ✓ Complete medium tasks (compare, extract) with 90%+ success
- ✓ Handle 80%+ of common errors (modals, paywalls, rate limits)
- ✓ Export data in 3 formats (JSON, CSV, API)
- ✓ Learn patterns (2nd run of same task is 30%+ faster)

### **Non-Functional Requirements**
- ✓ Max 20 steps per task (vs Level 2: 15 steps)
- ✓ Max 60s per step (includes LLM calls)
- ✓ Database queries <100ms
- ✓ Memory: <500MB per browser context
- ✓ Parallel 3-tab execution <3x slower than single-tab

### **Production Readiness**
- ✓ Comprehensive logging (all decisions logged to Phase E)
- ✓ Error reporting (blockers identified, categorized, recoverable)
- ✓ Monitoring (success rate, error rate, step duration)
- ✓ User API (REST endpoint for async job submission)
- ✓ Graceful degradation (if Phase G fails, continue without extraction)

---

## LEVEL 2 → LEVEL 3: WHAT CHANGES FOR USERS?

### **Level 2 Experience**
```
User: "Search for 'papper terminal' and find top result"
Level 2 Output: "Task completed" or "Task failed"
Problem: No result exported, can't use elsewhere
```

### **Level 3 Experience**
```
User: "Find 5 cheapest flights Delhi→Singapore, export as JSON"

Level 3 Output:
{
  "task_id": "flight_search_001",
  "status": "completed",
  "duration_seconds": 28,
  "flights": [
    {"price": 199, "airline": "AI", "date": "2026-05-05", "url": "..."},
    {"price": 210, "airline": "AA", "date": "2026-05-06", "url": "..."},
    ...
  ],
  "patterns_learned": ["flight-search", "price-extraction"],
  "errors_recovered": 1  // Modal closed automatically
}

Data usable in: Excel, API integration, reporting systems
```

---

## RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM extraction costs balloon | Budget | Use Haiku/GPT-3.5, cache results, limit to <5 extractions per task |
| Database queries slow down | Performance | Index by workflow_id, add query caching, rotate old data |
| Multi-tab context switching slow | UX | Limit to 3 tabs, prefetch next page while current loads |
| Hallucinated backoff waits | Timeout | Cap wait at 16s, log all retries for review |
| Modal bypass selector changes | Reliability | Update selectors monthly, log failures for manual review |

---

## QUESTIONS FOR USER APPROVAL

Before implementation:

1. **Phase E - Data Privacy:**
   - Store full action history (including URLs visited)?
   - Or only store: action_type, success/fail, timestamps?

2. **Phase G - LLM Model Choice:**
   - Use OpenRouter for fallback?
   - Preferred model: Claude 3 Haiku or GPT-3.5?

3. **Phase H - Max Tabs:**
   - Safe limit: 3 tabs? Or 5?
   - How to handle tab failure (one tab crashes)?

4. **Phase I - Rate Limit Backoff:**
   - Max wait time: 16s? Or flexible?
   - Give up after: 3 attempts or 5?

5. **Phase J - Data Export:**
   - Minimum accuracy for valid record: 95%? Or 90%?
   - Support which export formats: JSON, CSV, both?

---

## NEXT STEPS

If you approve this plan:
1. ✅ Lock the architecture (no changes mid-implementation)
2. ✅ Start Phase E (Week 1)
3. ✅ Weekly sync to catch issues early
4. ✅ User testing after Phase F (state verification working)
5. ✅ Production deployment after Phase J

**Bhai, agar ye plan theek lag raha hai, to hum Phase E se shuru kar sakte hain. Kya bolte ho?**
