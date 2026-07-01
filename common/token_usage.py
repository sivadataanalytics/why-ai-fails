# Token estimation (dry-run) and savings percentage helpers

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    # Rough chars/4 heuristic when Gemini API is not called (--dry-run)
    if not text:
        return 0
    return max(1, len(text) // 4)


def pct_reduction(before: float, after: float) -> float:
    if before <= 0:
        return 0.0
    return round(100.0 * (before - after) / before, 1)
