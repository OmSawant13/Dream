"""
Phase F: Autonomous Blocker Handler

Detects and handles common web obstacles:
    - Cookie consent banners
    - Modal popups ("Sign up", "Subscribe")
    - Captcha prompts
    - Rate limit warnings

The handler has two strategies:
    1. Memory-first: Check if we've successfully bypassed this blocker type
       at this URL before (via PersistentMemory's blocker table).
    2. Heuristic: Scan the grid for keywords like "accept", "close", "dismiss"
       and attempt to click the matching element.

Design decision: This runs BEFORE the normal planning loop each step.
If a blocker is detected and handled, the agent re-captures the grid
and continues — the LLM never sees the blocker at all.
"""

import logging

logger = logging.getLogger("papper-blocker")

# Keyword sets for each blocker type.
# Matched case-insensitively against the grid text.
BLOCKER_KEYWORDS = {
    "cookie_banner": [
        "accept cookies", "cookie policy", "agree", "i accept",
        "accept all", "cookie consent", "we use cookies",
    ],
    "modal": [
        "close", "dismiss", "×", "not now", "no thanks",
        "skip", "maybe later", "remind me later",
    ],
    "paywall": [
        "subscribe to continue", "sign up to read",
        "create account to continue", "premium content",
    ],
    "captcha": [
        "verify you are human", "i'm not a robot", "captcha",
        "security check", "prove you're not a robot",
    ],
    "rate_limit": [
        "too many requests", "slow down", "try again later",
        "rate limited", "please wait",
    ],
}

# For each blocker type, which keywords are safe to auto-click.
# We don't auto-click paywall or captcha buttons — those need human judgment.
SAFE_TO_CLICK = {
    "cookie_banner": ["accept all", "accept cookies", "i accept", "agree", "accept"],
    "modal": ["close", "dismiss", "×", "not now", "no thanks", "skip", "maybe later"],
}


class BlockerHandler:
    """Detect and autonomously handle web page blockers.

    This runs as a pre-check before each planning step. If a blocker is
    detected and successfully handled, the main loop re-captures state
    and continues without involving the LLM.
    """

    def __init__(self, observer, actions, persistent_memory):
        self.observer = observer
        self.actions = actions
        self.persistent = persistent_memory

    async def detect_and_handle(self, grid_text: str, url: str) -> bool:
        """Detect blockers in the current grid and attempt to handle them.

        Args:
            grid_text: The current grid text (from observer.capture_grid)
            url: The current page URL

        Returns:
            True if a blocker was detected AND successfully handled.
            False if no blocker found or handling failed.
        """
        grid_lower = grid_text.lower()

        for blocker_type, keywords in BLOCKER_KEYWORDS.items():
            if any(kw in grid_lower for kw in keywords):
                logger.info(f"🚫 Detected blocker: {blocker_type}")
                handled = await self._handle_blocker(
                    blocker_type, url, grid_text
                )
                if handled:
                    return True
                # Don't return False yet — might be a different blocker type

        return False

    async def _handle_blocker(
        self, blocker_type: str, url: str, grid_text: str
    ) -> bool:
        """Attempt to bypass a detected blocker.

        Strategy 1: Check persistent memory for a known bypass
        Strategy 2: Heuristic — find a clickable element matching safe keywords
        """
        # Strategy 1: Known bypass from memory
        bypass = self.persistent.get_blocker_bypass(blocker_type, url)
        if bypass:
            logger.info(f"📝 Found known bypass for {blocker_type}")
            index = bypass.get("index")
            if index is not None:
                result = await self.actions.click_index(str(index))
                if result.get("status") == "success":
                    self.persistent.record_blocker_outcome(
                        blocker_type, url, success=True
                    )
                    logger.info(f"✅ Known bypass worked for {blocker_type}")
                    return True
                else:
                    self.persistent.record_blocker_outcome(
                        blocker_type, url, success=False
                    )

        # Strategy 2: Heuristic — scan grid for safe-to-click keywords
        safe_keywords = SAFE_TO_CLICK.get(blocker_type, [])
        if not safe_keywords:
            logger.info(
                f"⚠️ No safe auto-click keywords for {blocker_type} — skipping"
            )
            return False

        # Parse grid to find element indices matching safe keywords
        for line in grid_text.split("\n"):
            line_lower = line.lower()
            for kw in safe_keywords:
                if kw in line_lower:
                    # Extract index from "[N] ROLE: "text""
                    idx = self._extract_index(line)
                    if idx is not None:
                        logger.info(
                            f"🔍 Heuristic: clicking [{idx}] "
                            f"matching '{kw}' for {blocker_type}"
                        )
                        result = await self.actions.click_index(str(idx))
                        if result.get("status") == "success":
                            # Learn this bypass for future use
                            self.persistent.learn_blocker(
                                blocker_type=blocker_type,
                                url_pattern=self._extract_domain(url),
                                detection_rule={"keyword": kw},
                                bypass_method={"action": "click", "index": idx},
                            )
                            logger.info(
                                f"✅ Heuristic bypass worked — learned for future"
                            )
                            return True

        logger.warning(f"⚠️ Could not bypass {blocker_type} at {url}")
        return False

    @staticmethod
    def _extract_index(grid_line: str):
        """Extract the element index from a grid line like '[3] BUTTON: "Accept"'.

        Returns int or None.
        """
        line = grid_line.strip()
        if line.startswith("["):
            bracket_end = line.find("]")
            if bracket_end > 1:
                try:
                    return int(line[1:bracket_end])
                except ValueError:
                    return None
        return None

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL for pattern storage.

        'https://www.amazon.com/products/123' → 'amazon.com'
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or url
            # Remove www. prefix
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return url
