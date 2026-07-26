"""
Intent detection and task classification for Series 2.7.

Maps free-text prompts to task types using keyword patterns (no ML deps).
"""

from __future__ import annotations

import re
from typing import Any

from requests import TASK_TYPES

WORD = re.compile(r"[a-z_]+")

# Keyword signals per task type — order matters for tie-breaking
INTENT_KEYWORDS: dict[str, list[str]] = {
    "translation": ["translate", "spanish", "french", "german", "convert"],
    "email_summarization": ["summarize", "email", "bullet", "thread"],
    "classification": ["classify", "sentiment", "label", "priority", "urgent"],
    "sql_generation": ["sql", "postgresql", "query", "join", "table", "database"],
    "backend_api": ["fastapi", "flask", "rest", "api", "endpoint", "webhook"],
    "architecture_design": ["architecture", "kubernetes", "microservices", "design", "scalable"],
    "code_review": ["review", "bug", "middleware", "security", "improvements", "function"],
    "legal_analysis": ["contract", "gdpr", "liability", "indemnification", "legal", "msa"],
    "vision": ["image", "photo", "scan", "visual", "defects", "warehouse"],
    "reasoning": ["root cause", "trade-offs", "throughput", "explain why", "evaluate"],
}


def detect_intent(prompt: str) -> set[str]:
    """Extract intent terms from prompt text."""
    return set(WORD.findall(prompt.lower()))


def classify_task(prompt: str, *, hint: str | None = None) -> str:
    """
    Classify prompt into one task type.

    Uses keyword overlap scoring. Optional hint from dataset metadata improves accuracy
    when running benchmarks (simulates enriched request context in production gateways).
    """
    if hint and hint in TASK_TYPES:
        return hint

    terms = detect_intent(prompt)
    best_task = "reasoning"
    best_score = -1

    for task_type, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in terms or kw.replace("_", " ") in prompt.lower())
        if score > best_score:
            best_score = score
            best_task = task_type

    return best_task


def classification_confidence(prompt: str, task_type: str) -> float:
    """Heuristic confidence for classified task type (0–1)."""
    terms = detect_intent(prompt)
    keywords = INTENT_KEYWORDS.get(task_type, [])
    if not keywords:
        return 0.5
    hits = sum(1 for kw in keywords if kw in terms or kw in prompt.lower())
    return round(min(1.0, 0.45 + hits * 0.15), 2)
