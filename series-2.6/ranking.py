"""
Memory ranking and top-K selection for Series 2.6.

Ranking formula (Hybrid + Re-ranking):
  Memory Score = Semantic Similarity + Confidence + Recency + Business Priority

Weights tuned for enterprise baseline — adjust experimentally in production.
"""

from __future__ import annotations

from typing import Any

# Weights for final re-ranking stage
WEIGHT_SEMANTIC = 0.40
WEIGHT_CONFIDENCE = 0.20
WEIGHT_RECENCY = 0.20
WEIGHT_PRIORITY = 0.20


def rank_score(
    memory: dict[str, Any],
    *,
    semantic_similarity: float,
) -> float:
    """
    Combined ranking score for re-ranking stage.

    Memory Score = w1*semantic + w2*confidence + w3*recency + w4*business_priority
    """
    return (
        WEIGHT_SEMANTIC * semantic_similarity
        + WEIGHT_CONFIDENCE * memory["confidence"]
        + WEIGHT_RECENCY * memory["recency"]
        + WEIGHT_PRIORITY * memory["business_priority"]
    )


def rerank(
    candidates: list[tuple[float, dict[str, Any]]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Re-rank top candidates using full ranking formula.

    Input: list of (semantic_similarity, memory) from hybrid retrieval
    Output: top_k memories with rank_score attached
    """
    scored: list[tuple[float, dict[str, Any], float]] = []
    for semantic_sim, mem in candidates:
        score = rank_score(mem, semantic_similarity=semantic_sim)
        scored.append((score, mem, semantic_sim))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    for rank, (score, mem, sem) in enumerate(scored[:top_k], start=1):
        entry = dict(mem)
        entry["rank_score"] = round(score, 4)
        entry["semantic_similarity"] = round(sem, 4)
        entry["rank"] = rank
        results.append(entry)
    return results


def select_top_k(
    scored: list[tuple[float, dict[str, Any]]],
    top_k: int,
    *,
    diverse_keys: bool = True,
) -> list[dict[str, Any]]:
    """
    Select top-K from pre-scored candidates.

    diverse_keys=True avoids 5 duplicate FastAPI memories — prefers one per key.
    """
    scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for score, mem in scored_sorted:
        if diverse_keys and mem["key"] in seen_keys:
            continue
        seen_keys.add(mem["key"])
        entry = dict(mem)
        entry["retrieval_score"] = round(score, 4)
        entry["rank"] = len(results) + 1
        results.append(entry)
        if len(results) >= top_k:
            break

    # Fill remaining slots if diversity filter left gaps
    if len(results) < top_k:
        for score, mem in scored_sorted:
            if any(r["memory_id"] == mem["memory_id"] for r in results):
                continue
            entry = dict(mem)
            entry["retrieval_score"] = round(score, 4)
            entry["rank"] = len(results) + 1
            results.append(entry)
            if len(results) >= top_k:
                break

    return results


def select_top_k_diverse_values(
    scored: list[tuple[float, dict[str, Any]]],
    top_k: int,
) -> list[dict[str, Any]]:
    """
    Top-K with one memory per canonical value — reduces prompt noise from duplicates.

    Re-ranking stage prefers distinct facts (Python, FastAPI, Secure Coding) over
    five copies of the same framework preference.
    """
    scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    seen_values: set[str] = set()

    for score, mem in scored_sorted:
        if mem["value"] in seen_values:
            continue
        seen_values.add(mem["value"])
        entry = dict(mem)
        entry["retrieval_score"] = round(score, 4)
        entry["rank"] = len(results) + 1
        results.append(entry)
        if len(results) >= top_k:
            break

    return results
