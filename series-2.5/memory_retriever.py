"""
Memory retrieval for Series 2.5.

Pipeline:
  User Request → intent keywords → memory search → ranking → Top K

Uses keyword overlap + category hints (no vector DB — readable for students).
"""

from __future__ import annotations

import re
from typing import Any

WORD_PATTERN = re.compile(r"[a-z0-9]+")

# Map question intents to relevant memory categories
INTENT_CATEGORY_MAP: dict[str, list[str]] = {
    "fastapi": ["User Preferences", "Technical Constraints"],
    "secure": ["Organization Standards", "Security Rules"],
    "python": ["User Preferences", "Coding Style"],
    "database": ["Technical Constraints"],
    "postgres": ["Technical Constraints"],
    "framework": ["User Preferences"],
    "organization": ["Organization Standards", "Coding Style"],
    "standards": ["Organization Standards"],
    "code": ["Coding Style", "User Preferences"],
}


def _words(text: str) -> set[str]:
    return set(WORD_PATTERN.findall(text.lower()))


def detect_intents(question: str, extra_keywords: list[str] | None = None) -> set[str]:
    """Simple intent detection from question text + optional keyword hints."""
    intents = _words(question)
    if extra_keywords:
        intents |= {k.lower() for k in extra_keywords}
    return intents


def score_memory(memory: dict[str, Any], intents: set[str]) -> float:
    """
    Rank memories by relevance to detected intents.

    Scoring:
      - word overlap between intent and memory value/key
      - category boost when intent maps to category
      - confidence weight
    """
    mem_text = f"{memory['key']} {memory['value']} {memory['category']}".lower()
    mem_words = _words(mem_text)
    overlap = len(intents & mem_words)

    category_boost = 0.0
    for intent in intents:
        for cat in INTENT_CATEGORY_MAP.get(intent, []):
            if cat == memory["category"]:
                category_boost += 1.5

    if "fastapi" in intents or "rest" in intents or "api" in intents:
        category_boost += 2.0
        if memory.get("value") == "FastAPI" or "fastapi" in memory.get("value", "").lower():
            category_boost += 3.0
        if memory.get("key") == "backend_stack":
            category_boost += 2.5

    return overlap * 2.0 + category_boost + memory["confidence"]


def retrieve_top_k(
    question: str,
    memories: list[dict[str, Any]],
    *,
    top_k: int = 5,
    intent_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return top-k relevant memories for the user request."""
    if not memories:
        return []

    intents = detect_intents(question, intent_keywords)
    scored = [(score_memory(m, intents), m) for m in memories]
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[dict[str, Any]] = []
    for rank, (score, mem) in enumerate(scored[:top_k], start=1):
        entry = dict(mem)
        entry["retrieval_score"] = round(score, 2)
        entry["rank"] = rank
        results.append(entry)
    return results
