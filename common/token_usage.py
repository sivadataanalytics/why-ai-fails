"""
Token counting helpers.

estimate_tokens() — rough chars/4 estimate for --dry-run (no API call, $0)
pct_reduction()   — calculate % tokens saved by pruning
"""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """
    Estimate prompt tokens without calling Gemini.

    Used by --dry-run to compare pruned vs unpruned prompt sizes for free.
    Rule of thumb: ~4 characters per token for English text.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def pct_reduction(before: float, after: float) -> float:
    """Calculate percentage reduction. before=unpruned, after=pruned."""
    if before <= 0:
        return 0.0
    return round(100.0 * (before - after) / before, 1)


# ---------------------------------------------------------------------------
# Demo pricing (USD per 1 million tokens) — provider-neutral placeholders
#
#   INPUT_COST_PER_M         full-price input tokens
#   CACHED_INPUT_COST_PER_M  cached static tokens (~75% cheaper in this demo)
#   OUTPUT_COST_PER_M        completion / output tokens
# ---------------------------------------------------------------------------
INPUT_COST_PER_M = 0.075
OUTPUT_COST_PER_M = 0.30
CACHED_INPUT_COST_PER_M = 0.01875


def estimate_input_cost(prompt_tokens: int, *, cached_prompt_tokens: int = 0) -> float:
    """
    Input-side cost only — the part prompt caching reduces.

    Two billing modes:

    CACHE MISS (cached_prompt_tokens = 0):
      All prompt_tokens are fresh → full INPUT_COST_PER_M rate.

    CACHE HIT (cached_prompt_tokens > 0):
      prompt_tokens     = fresh input only (dynamic + cache reference)
      cached_prompt_tokens = static block billed at CACHED_INPUT_COST_PER_M

    Example (hit path): prompt_tokens=156, cached_prompt_tokens=366
      fresh  = 156  @ $0.075/M  (dynamic + cache ref)
      cached = 366  @ $0.019/M  (static block at discount)
    """
    if cached_prompt_tokens > 0:
        fresh = prompt_tokens
        cached = cached_prompt_tokens
    else:
        fresh = prompt_tokens
        cached = 0
    return round(
        (fresh * INPUT_COST_PER_M + cached * CACHED_INPUT_COST_PER_M) / 1_000_000, 6
    )


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    *,
    cached_prompt_tokens: int = 0,
) -> float:
    """Total request cost = input cost + output cost."""
    input_cost = estimate_input_cost(
        prompt_tokens, cached_prompt_tokens=cached_prompt_tokens
    )
    output_cost = completion_tokens * OUTPUT_COST_PER_M / 1_000_000
    return round(input_cost + output_cost, 6)
