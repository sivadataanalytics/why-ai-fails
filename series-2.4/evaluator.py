"""
Memory quality evaluation for Series 2.4.

Memory Score answers: "Did summarization preserve the important facts?"

  Memory Score = remembered facts / expected facts

Example:
  Expected facts: 9  (Python, Prompt Caching, benchmark, ...)
  Matched in context: 9
  Memory Score: 1.00

Context checked = memory_text + latest_messages (what Gemini would see).
Full conversation strategy uses all messages as latest_messages.
"""

from __future__ import annotations

from typing import Any

from conversation_dataset import EXPECTED_MEMORY_FACTS


def _context_text(memory_text: str, latest_messages: list[dict[str, Any]]) -> str:
    """
    Combine all text the model receives into one searchable string.

    For summarization strategies: memory summary + recent verbatim messages.
    For full strategy: memory_text is empty, latest_messages is the full history.
    """
    parts = [memory_text] if memory_text else []
    parts.extend(m["content"] for m in latest_messages)
    return "\n".join(parts)


def memory_score(
    memory_text: str,
    latest_messages: list[dict[str, Any]],
    expected_facts: list[str] | None = None,
) -> float:
    """
    Calculate Memory Score for one strategy.

    A fact "matches" if its text appears (case-insensitive) anywhere in the
    combined context. Simple but understandable for students.

    Returns 0.0–1.0 (1.0 = all expected facts preserved).
    """
    facts = expected_facts or EXPECTED_MEMORY_FACTS
    if not facts:
        return 1.0

    combined = _context_text(memory_text, latest_messages).lower()
    matched = sum(1 for fact in facts if fact.lower() in combined)
    return round(matched / len(facts), 2)


def matched_facts(
    memory_text: str,
    latest_messages: list[dict[str, Any]],
    expected_facts: list[str] | None = None,
) -> list[str]:
    """Return which expected facts were found — printed in dry-run memory detail."""
    facts = expected_facts or EXPECTED_MEMORY_FACTS
    combined = _context_text(memory_text, latest_messages).lower()
    return [fact for fact in facts if fact.lower() in combined]


def context_retention(strategy_score: float, full_score: float) -> float:
    """
    Context retention relative to full conversation baseline.

    Full conversation = 1.00 reference.
    If a strategy scores 0.89 vs full 1.00 → retention = 0.89.

    Capped at 1.0 (strategies cannot exceed full conversation memory).
    """
    if full_score <= 0:
        return strategy_score
    return round(min(1.0, strategy_score / full_score), 2)
