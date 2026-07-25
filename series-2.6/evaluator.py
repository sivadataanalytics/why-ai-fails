"""
Evaluation metrics for Series 2.6 memory retrieval lab.

Retrieval Accuracy — expected values found in top-K results
Precision            — relevant memories / total retrieved
Recall               — relevant memories / total relevant in store for query
Personalization      — query-specific expected value coverage
"""

from __future__ import annotations

from typing import Any

from memories import CANONICAL_TEMPLATES, EXPECTED_MEMORIES


def _combined_text(memories: list[dict[str, Any]]) -> str:
    return " ".join(
        f"{m['value']} {m['text']} {' '.join(m.get('tags', []))}" for m in memories
    ).lower()


def _memory_matches_value(mem: dict[str, Any], value: str) -> bool:
    val_lower = value.lower()
    blob = _combined_text([mem])
    return val_lower in blob


def is_relevant_to_query(mem: dict[str, Any], expected_values: list[str]) -> bool:
    """True if memory matches any expected value and is not obsolete."""
    if mem.get("obsolete"):
        return False
    return any(_memory_matches_value(mem, ev) for ev in expected_values)


def retrieval_accuracy(
    retrieved: list[dict[str, Any]],
    expected_values: list[str],
) -> float:
    """
    Top-K accuracy: fraction of expected values found in retrieved memories.

    Same intuitive metric as Series 2.3 Hit Score / Series 2.5 Memory Score.
    """
    if not expected_values:
        return 1.0
    combined = _combined_text(retrieved)
    matched = sum(1 for ev in expected_values if ev.lower() in combined)
    return round(matched / len(expected_values), 2)


def precision(
    retrieved: list[dict[str, Any]],
    expected_values: list[str],
) -> float:
    """Precision = relevant retrieved / total retrieved."""
    if not retrieved:
        return 0.0
    relevant_count = sum(1 for m in retrieved if is_relevant_to_query(m, expected_values))
    return round(relevant_count / len(retrieved), 2)


def recall(
    retrieved: list[dict[str, Any]],
    all_memories: list[dict[str, Any]],
    expected_values: list[str],
) -> float:
    """
    Recall = relevant retrieved / total relevant in store.

    Uses canonical templates as the relevance definition to avoid inflating
    denominator with thousands of duplicate Python memories.
    """
    canonical_values = {t["value"] for t in CANONICAL_TEMPLATES if t["value"] in expected_values}
    if not canonical_values:
        canonical_values = set(expected_values)

    total_relevant = len(canonical_values)
    combined = _combined_text(retrieved)
    found = sum(1 for v in canonical_values if v.lower() in combined)
    return round(found / total_relevant, 2) if total_relevant else 0.0


def personalization_score(
    retrieved: list[dict[str, Any]],
    expected_values: list[str],
) -> float:
    """Query-specific personalization — weighted retrieval accuracy."""
    return retrieval_accuracy(retrieved, expected_values)


def matched_values(
    retrieved: list[dict[str, Any]],
    expected_values: list[str],
) -> list[str]:
    combined = _combined_text(retrieved)
    return [ev for ev in expected_values if ev.lower() in combined]
