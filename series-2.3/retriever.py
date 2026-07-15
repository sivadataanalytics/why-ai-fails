"""
Simple keyword retriever for Series 2.3.

No vector database — students can read and understand the scoring logic.

Scoring:
  1. Tokenize question and chunk text into words (lowercase, alphanumeric)
  2. Score = count of question words found in chunk
  3. Rank descending, return top-k

Hit Score (retrieval quality):
  matched expected_terms in retrieved chunks / total expected_terms
"""

from __future__ import annotations

import re
from typing import Any

WORD_PATTERN = re.compile(r"[a-z0-9]+")


def _words(text: str) -> set[str]:
    return set(WORD_PATTERN.findall(text.lower()))


def score_chunk(question: str, chunk: dict[str, Any]) -> float:
    """Keyword overlap score — higher means more relevant."""
    q_words = _words(question)
    if not q_words:
        return 0.0
    c_words = _words(chunk["text"])
    overlap = q_words & c_words
    return float(len(overlap))


def retrieve_top_k(
    question: str,
    chunks: list[dict[str, Any]],
    *,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return top-k chunks ranked by keyword score."""
    if not chunks:
        return []

    scored = [(score_chunk(question, chunk), chunk) for chunk in chunks]
    scored.sort(key=lambda item: item[0], reverse=True)

    results: list[dict[str, Any]] = []
    for rank, (score, chunk) in enumerate(scored[:top_k], start=1):
        entry = dict(chunk)
        entry["retrieval_score"] = round(score, 2)
        entry["rank"] = rank
        results.append(entry)
    return results


def hit_score(retrieved: list[dict[str, Any]], expected_terms: list[str]) -> float:
    """
    Simple retrieval quality metric.

    Hit Score = matched expected terms / total expected terms

    A term matches if it appears (case-insensitive) in any retrieved chunk text.
    """
    if not expected_terms:
        return 1.0

    combined = " ".join(c["text"] for c in retrieved).lower()
    matched = sum(1 for term in expected_terms if term.lower() in combined)
    return round(matched / len(expected_terms), 2)


def matched_terms(retrieved: list[dict[str, Any]], expected_terms: list[str]) -> list[str]:
    """Return which expected terms were found — useful for debugging."""
    combined = " ".join(c["text"] for c in retrieved).lower()
    return [term for term in expected_terms if term.lower() in combined]
