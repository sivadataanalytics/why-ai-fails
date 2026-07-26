"""
Complexity estimation for Series 2.7.

Classifies requests as simple, medium, or complex using prompt signals.
"""

from __future__ import annotations

import re

from classifier import detect_intent

COMPLEXITIES = ("simple", "medium", "complex")

SIMPLE_SIGNALS = {"translate", "hello", "classify", "sentiment", "label", "summarize"}
MEDIUM_SIGNALS = {"sql", "query", "api", "review", "image", "endpoint", "postgresql"}
COMPLEX_SIGNALS = {
    "architecture",
    "kubernetes",
    "design",
    "legal",
    "contract",
    "reasoning",
    "trade-offs",
    "microservices",
    "gdpr",
}


def estimate_complexity(
    prompt: str,
    *,
    task_type: str | None = None,
    context_tokens: int = 0,
) -> str:
    """
    Estimate complexity tier from prompt keywords, task type, and context size.

    Examples:
      Simple  — "Translate Hello"
      Medium  — "Generate SQL ..."
      Complex — "Design Kubernetes Architecture"
    """
    terms = detect_intent(prompt)
    lower = prompt.lower()

    if task_type in ("translation", "classification", "email_summarization"):
        base = "simple"
    elif task_type in ("sql_generation", "backend_api", "code_review", "vision"):
        base = "medium"
    elif task_type in ("architecture_design", "legal_analysis", "reasoning"):
        base = "complex"
    else:
        base = "medium"

    complex_hits = sum(1 for s in COMPLEX_SIGNALS if s in terms or s in lower)
    simple_hits = sum(1 for s in SIMPLE_SIGNALS if s in terms or s in lower)

    if complex_hits >= 2 or context_tokens > 450:
        return "complex"
    if simple_hits >= 2 and complex_hits == 0 and context_tokens < 200:
        return "simple"
    if base == "complex" or complex_hits >= 1:
        return "complex"
    if base == "simple" and simple_hits >= 1:
        return "simple"
    return "medium"


def complexity_score(complexity: str) -> float:
    """Numeric score for router cost/quality trade-offs."""
    return {"simple": 0.25, "medium": 0.55, "complex": 0.90}[complexity]
