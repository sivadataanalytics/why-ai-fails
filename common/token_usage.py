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
