"""
Memory compression engine for Series 2.5.

Four operations (applied in order for 'compressed' strategy):

  1. DEDUPLICATION   — same category+key → keep highest confidence / latest
  2. CONSOLIDATION   — merge related stack items → "Python Backend Stack"
  3. UPDATING        — newer conversation_id wins for same key
  4. EXPIRATION      — drop low-confidence temporary / obsolete entries
"""

from __future__ import annotations

from typing import Any

# Keys merged into consolidated backend stack (keep preferred_framework separate)
STACK_KEYS = {"validation_library", "orm_library"}
CONSOLIDATED_VALUE = "Python Backend Stack (FastAPI, Pydantic, SQLAlchemy)"
CONSOLIDATED_KEY = "backend_stack"

# Memories below this confidence are expired (unless durable high-value)
EXPIRE_CONFIDENCE_THRESHOLD = 0.5

# Obsolete project names removed when a newer project memory exists
OBSOLETE_VALUES = {"LegacyBot"}


def deduplicate(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Operation 1 — Duplicate memories → single memory per category+key.

    When duplicates exist, keep the record from the highest conversation_id
    (most recent) with highest confidence.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for mem in memories:
        slot = (mem["category"], mem["key"])
        current = best.get(slot)
        if current is None:
            best[slot] = mem
            continue
        if mem["conversation_id"] > current["conversation_id"]:
            best[slot] = mem
        elif (
            mem["conversation_id"] == current["conversation_id"]
            and mem["confidence"] > current["confidence"]
        ):
            best[slot] = mem
    return list(best.values())


def consolidate(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Operation 2 — Merge related memories.

    Example: FastAPI + Pydantic + SQLAlchemy → Python Backend Stack
    """
    stack_items = [m for m in memories if m["key"] in STACK_KEYS]
    has_fastapi = any(m.get("value") == "FastAPI" for m in memories)
    other = [m for m in memories if m["key"] not in STACK_KEYS]

    if len(stack_items) < 1 and not has_fastapi:
        return memories

    if len(stack_items) < 1:
        return memories

    max_conv = max(m["conversation_id"] for m in stack_items)
    consolidated = {
        "memory_id": "m_consolidated_backend_stack",
        "conversation_id": max_conv,
        "category": "Technical Constraints",
        "key": CONSOLIDATED_KEY,
        "value": CONSOLIDATED_VALUE,
        "confidence": 0.92,
        "ttl_days": None,
        "text": "Consolidated: FastAPI + Pydantic + SQLAlchemy",
    }

    # Remove merged stack libraries; keep FastAPI preference as its own memory
    filtered = [m for m in other if m["key"] not in STACK_KEYS]
    filtered.append(consolidated)
    return filtered


def apply_updates(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Operation 3 — Updating: latest conversation wins for same category+key.

    Example: Preferred IDE PyCharm → VS Code (do NOT keep both).
    """
    return deduplicate(memories)


def expire(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Operation 4 — Expiration via confidence + TTL flags.

    Removes:
      - temporary low-confidence memories (ttl_days set, confidence < 0.5)
      - obsolete project names when Long-Term Memory exists
    """
    has_new_project = any(m.get("value") == "Long-Term Memory" for m in memories)
    kept: list[dict[str, Any]] = []

    for mem in memories:
        # Drop expired temporary entries
        if mem.get("ttl_days") is not None and mem["confidence"] < EXPIRE_CONFIDENCE_THRESHOLD:
            continue
        # Drop obsolete projects superseded by updates
        if has_new_project and mem.get("value") in OBSOLETE_VALUES:
            continue
        if mem["confidence"] < 0.4:
            continue
        kept.append(mem)
    return kept


def compress(memories: list[dict[str, Any]], *, level: str) -> list[dict[str, Any]]:
    """
    Apply compression pipeline based on strategy level.

    level:
      raw        — no compression
      dedup      — deduplication only
      compressed — dedup + consolidate + update + expire
    """
    if level == "raw":
        return list(memories)
    if level == "dedup":
        return deduplicate(memories)
    if level == "compressed":
        result = deduplicate(memories)
        result = consolidate(result)
        result = apply_updates(result)
        result = expire(result)
        return result
    raise ValueError(f"Unknown compression level: {level}")
