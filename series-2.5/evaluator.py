"""
Evaluation metrics for Series 2.5 long-term memory lab.

Retrieval Accuracy = matched expected memories / total expected memories

Also tracks Memory Quality and Personalization Accuracy (same formula,
optionally against question-specific expected sets).
"""

from __future__ import annotations

from typing import Any

from conversations import EXPECTED_MEMORIES


def _context_text(memories: list[dict[str, Any]]) -> str:
    return " ".join(f"{m['key']} {m['value']} {m['category']}" for m in memories).lower()


def retrieval_accuracy(
    retrieved: list[dict[str, Any]],
    expected: list[str] | None = None,
) -> float:
    """
    Retrieval Accuracy = retrieved expected / total expected

    A memory "matches" if expected term appears in any retrieved value/key/category.
    """
    targets = expected or EXPECTED_MEMORIES
    if not targets:
        return 1.0
    combined = _context_text(retrieved)
    matched = sum(1 for term in targets if term.lower() in combined)
    return round(matched / len(targets), 2)


def matched_memories(
    retrieved: list[dict[str, Any]],
    expected: list[str] | None = None,
) -> list[str]:
    """Which expected memory terms were found in retrieval results."""
    targets = expected or EXPECTED_MEMORIES
    combined = _context_text(retrieved)
    return [term for term in targets if term.lower() in combined]


def memory_quality(store_size: int, raw_size: int) -> float:
    """
    Memory Quality proxy: compression ratio preserved as quality per token.

    1.0 = same size as raw (no compression benefit).
    Lower store_size vs raw_size → higher quality per stored token.
    """
    if raw_size <= 0:
        return 1.0
    ratio = store_size / raw_size
    return round(max(0.1, min(1.0, ratio)), 2)


def personalization_accuracy(
    retrieved: list[dict[str, Any]],
    question_expected: list[str],
) -> float:
    """Per-question personalization — did retrieval surface user-specific facts?"""
    return retrieval_accuracy(retrieved, question_expected)
