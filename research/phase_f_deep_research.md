# Phase F Deep Research: Deterministic Browser Agents

This document outlines the architectural patterns and code-level logic derived from researching industry-standard browser automation engines, primarily **Microsoft Playwright**. These findings serve as the foundation for Papper Agent's Phase F transition from naive hashing to a signal-based deterministic engine.

---

## 🏗️ 1. Stability & Readiness Signals (The "Waiter" Pattern)

### 🔹 The Problem with Naive Hashing
Naive hashing (capturing the DOM and comparing hashes) fails because:
- **Animations**: A button moving by 1px results in a different hash.
- **Lazy Loading**: Content appearing after the snapshot renders the hash stale.
- **Dynamic Content**: Timestamps or randomly generated IDs break consistency.

### 🔹 Playwright's Solution: RAF Stability
Playwright doesn't just wait for a timeout; it waits for **visual stability** using `requestAnimationFrame` (RAF).

**Key Logic (Simplified):**
```typescript
async function checkElementIsStable(element: Element): Promise<boolean> {
  const getBox = () => element.getBoundingClientRect();
  let stableRafCount = 0;
  let lastBox = getBox();

  while (stableRafCount < 5) { // Wait for 5 consecutive stable frames
    await new Promise(requestAnimationFrame);
    const currentBox = getBox();
    if (boxesAreEqual(currentBox, lastBox)) {
      stableRafCount++;
    } else {
      stableRafCount = 0;
      lastBox = currentBox;
    }
  }
  return true;
}
```

> [!TIP]
> **Papper Mapping**: Implement a similar stability check in `agent/_wait_for_stability`. Instead of just `asyncio.sleep`, we should capture the grid/hash twice with a short delay and only proceed if they are identical.

---

## 🛡️ 2. Blocker Handling (Locator Handlers)

### 🔹 The Pattern: Pre-Action Interceptors
Playwright implements "Locator Handlers" (checkpoints) that run before any action (click, type).

**Key Architectural Snippet (`page.ts`):**
```typescript
async function performActionPreChecks() {
  // 1. Wait for main frame navigation to settle
  await this._mainFrame.waitForNavigationInternal();

  // 2. Run registered 'blocker' handlers
  for (const handler of this._locatorHandlers) {
    if (await handler.isVisible()) {
      await handler.resolve(); // e.g., click "Accept Cookies"
    }
  }
}
```

> [!IMPORTANT]
> **Papper Mapping**: The `BlockerHandler` should maintain a "Blacklist" of common selectors (cookie banners, modals). Before every LLM-planned action, the agent should run a quick `BlockerHandler.detect_and_clear()` call.

---

## 🔍 3. Event Safety (Hit-Target Interception)

### 🔹 The Pattern: Event-Time Verification
One of the most robust features in Playwright is the **Hit-Target Interceptor**. It ensures that between the time the agent "decides" to click and the "actual" click, no modal has appeared on top.

**Logic:**
- Inject a script that attaches a one-time `mousedown` listener at the window level.
- When the event fires, check `document.elementFromPoint(x, y)`.
- If the element is NOT the target (or its child), abort and retry.

---

## 📸 4. Visual Verification (Deterministic Comparison)

### 🔹 The Pattern: The "Double Stable" Screenshot
When verifying if an action worked, Playwright's `expectScreenshot` uses a retry loop with increasing backoff. It requires **two consecutive screenshots to be identical** before it considers the page "settled" for comparison.

**Intervals:** `[0, 100, 250, 500, 1000]ms`

> [!NOTE]
> **Papper Mapping**: `StateVerifier` should adopt this. Instead of one snapshot post-action, take two. If they differ, the page is still "transitioning" (loading/animating).

---

## 🛠️ Phase F Implementation Strategy

### 1. `StateVerifier` (Signals over Hashes)
Instead of a single boolean `changed`, return a **Signal Object**:
- `url_changed`: Boolean
- `dom_structure_changed`: (Ignoring text/values)
- `interactive_elements_changed`: (New buttons/inputs)
- `is_stable`: (Consecutive matches)

### 2. `LoopResolver` (Strategic Recovery)
When a loop is detected (3+ identical states), don't just "try again".
- **Analyze the Blocker**: Is there a persistent element at the click coordinates?
- **Analyze the Action**: Did a `click` result in `NO_CHANGE`? (Maybe it's a dead link or requires a double-click).
- **LLM Context**: Inject the *specific* failure signal: `[SIGNAL]: Clicked Button A but URL and DOM remained identical for 3 attempts.`

### 3. `BlockerHandler` (Autonomous Mitigation)
- **Memory-Based Detection**: If the agent successfully closed a modal once, store the "Mitigation Pattern" (Selector + Action) and apply it automatically if the modal reappears.

---

## 📜 References
- [Playwright Waiter.ts](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/waiter.ts)
- [Playwright Injected Scripts](https://github.com/microsoft/playwright/tree/main/packages/playwright-core/src/server/injected)
- [Papper Agent Phase F Plan](file:///Users/omsawant/Desktop/Projects/Dream/repo_study/PHASE_F_IMPLEMENTATION.md)
