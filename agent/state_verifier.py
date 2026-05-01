"""
Phase F: State Verification Engine

The core insight from Playwright/Cypress research:
    Don't ask "did the hash change?" — ask "WHAT changed and does it matter?"

StateVerifier classifies every action's outcome into one of 4 categories:
    NAVIGATION — URL changed (strongest signal of progress)
    CONTENT    — Same URL, but page text changed (AJAX, search results loaded)
    UI_ONLY    — Only visual change (hover effect, animation, dropdown opened)
    NO_CHANGE  — Nothing changed at all (dead click, broken element)

ContextBuilder converts these signals into human-readable feedback for the LLM,
so the planner knows what its last action actually accomplished.
"""

from dataclasses import dataclass
from typing import Literal

ChangeType = Literal["NAVIGATION", "CONTENT", "UI_ONLY", "NO_CHANGE"]


@dataclass
class StateChange:
    """Immutable result of comparing two browser states.

    This is what flows through the system — every component reads this
    rather than doing its own comparison.
    """
    change_type: ChangeType
    url_changed: bool
    visual_changed: bool
    text_changed: bool
    before_url: str
    after_url: str


class StateVerifier:
    """Classify state transitions using deterministic signal hierarchy.

    Priority order (from Playwright research):
        1. URL change → NAVIGATION (always the strongest signal)
        2. Text hash change → CONTENT (real data changed)
        3. Visual hash change only → UI_ONLY (CSS/animation noise)
        4. Nothing → NO_CHANGE (action had zero effect)

    Cost: 0 LLM tokens. Pure hash comparison.
    """

    def verify(
        self,
        before_url: str,
        after_url: str,
        before_visual: str,
        after_visual: str,
        before_text: str,
        after_text: str,
    ) -> StateChange:
        """Compare before/after state and classify the transition.

        Args:
            before_url: URL before action
            after_url: URL after action
            before_visual: Screenshot hash before action
            after_visual: Screenshot hash after action
            before_text: Grid text hash before action
            after_text: Grid text hash after action

        Returns:
            StateChange with classified change_type and individual flags
        """
        url_changed = before_url != after_url
        visual_changed = before_visual != after_visual
        text_changed = before_text != after_text

        # Priority hierarchy: URL > Text > Visual > Nothing
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
    """Convert StateChange into semantic feedback for the LLM planner.

    The key insight: LLMs repeat failed actions because they don't know
    the action failed. By injecting "[STATE AFTER LAST ACTION]: NO_CHANGE"
    into the prompt, the LLM has the information it needs to change strategy.

    Cost: ~60 tokens per message (trivial).
    """

    # Lookup table: (action_type, change_type) → human message
    # Every combination the agent can produce is covered.
    _MESSAGES = {
        # type action outcomes
        ("type",      "NO_CHANGE"):  "Last type had NO effect. Input may need Enter or Submit button to trigger.",
        ("type",      "CONTENT"):    "Last type updated page content as expected.",
        ("type",      "UI_ONLY"):    "Last type caused only visual change — content unchanged. Try pressing Enter.",
        ("type",      "NAVIGATION"): "Last type triggered navigation to: {after_url}.",
        # click action outcomes
        ("click",     "NO_CHANGE"):  "Last click caused NO change. Element may be decorative or disabled. Try a different element.",
        ("click",     "NAVIGATION"): "Last click navigated to a new URL: {after_url}. Verify this is the correct destination.",
        ("click",     "CONTENT"):    "Last click updated page content (likely AJAX/modal). Check new elements in grid.",
        ("click",     "UI_ONLY"):    "Last click caused visual change only (hover/animation). Core content unchanged.",
        # navigate action outcomes
        ("navigate",  "NAVIGATION"): "Navigation succeeded. Now at: {after_url}.",
        ("navigate",  "NO_CHANGE"):  "Navigation had no effect — URL may be the same or page didn't load.",
        ("navigate",  "CONTENT"):    "Navigation loaded new content at the same URL.",
        # press_key action outcomes
        ("press_key", "CONTENT"):    "Key press triggered content change. Check new elements.",
        ("press_key", "NO_CHANGE"):  "Key press had no effect. Try a different approach.",
        ("press_key", "NAVIGATION"): "Key press triggered navigation to: {after_url}.",
        ("press_key", "UI_ONLY"):    "Key press caused only visual change. Content unchanged.",
        # scroll action outcomes
        ("scroll",    "CONTENT"):    "Scroll revealed new content.",
        ("scroll",    "NO_CHANGE"):  "Scroll had no effect — may be at page boundary.",
        ("scroll",    "UI_ONLY"):    "Scroll caused visual shift but no new content loaded.",
        # wait action outcomes
        ("wait",      "CONTENT"):    "Wait completed — new content appeared.",
        ("wait",      "NO_CHANGE"):  "Wait completed — no changes detected.",
    }

    def build(self, state_change: StateChange, action_type: str) -> str:
        """Convert a StateChange into an LLM-ready context message.

        Args:
            state_change: The classified state transition
            action_type: The action that was just executed

        Returns:
            String like "[STATE AFTER LAST ACTION]: Last click caused NO change..."
        """
        key = (action_type, state_change.change_type)
        template = self._MESSAGES.get(
            key,
            f"Action '{action_type}' resulted in: {state_change.change_type}."
        )

        msg = template.format(
            after_url=state_change.after_url,
            before_url=state_change.before_url,
        )

        return f"[STATE AFTER LAST ACTION]: {msg}"
