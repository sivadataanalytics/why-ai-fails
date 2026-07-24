"""
Extract structured memories from conversations — Series 2.5.

Each user turn is scanned for durable facts. Output is a list of MemoryRecord
dicts ready for compression and storage.

Categories:
  - User Preferences
  - Project Information
  - Coding Style
  - Organization Standards
  - Security Rules
  - Technical Constraints
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# EXTRACTION RULES — (pattern, category, key, value, confidence, ttl_days?)
# ttl_days=None means durable; small TTL = temporary memory
# ---------------------------------------------------------------------------
EXTRACTION_RULES: list[tuple[re.Pattern[str], str, str, str, float, int | None]] = [
    (
        re.compile(r"prefer python|preferred language.*python|python with readable", re.I),
        "User Preferences",
        "preferred_language",
        "Python",
        0.95,
        None,
    ),
    (
        re.compile(r"fastapi|rest apis using fastapi", re.I),
        "User Preferences",
        "preferred_framework",
        "FastAPI",
        0.95,
        None,
    ),
    (
        re.compile(r"readable python|readable, well-typed|clear naming", re.I),
        "Coding Style",
        "coding_style",
        "Readable Python",
        0.9,
        None,
    ),
    (
        re.compile(r"secure coding|never store credentials|organization requires secure", re.I),
        "Organization Standards",
        "secure_coding",
        "Secure Coding",
        0.95,
        None,
    ),
    (
        re.compile(r"postgresql|postgres", re.I),
        "Technical Constraints",
        "database",
        "PostgreSQL",
        0.9,
        None,
    ),
    (
        re.compile(r"pydantic", re.I),
        "Technical Constraints",
        "validation_library",
        "Pydantic",
        0.85,
        None,
    ),
    (
        re.compile(r"sqlalchemy", re.I),
        "Technical Constraints",
        "orm_library",
        "SQLAlchemy",
        0.85,
        None,
    ),
    (
        re.compile(r"preferred ide.*pycharm|ide is pycharm", re.I),
        "User Preferences",
        "preferred_ide",
        "PyCharm",
        0.8,
        None,
    ),
    (
        re.compile(r"preferred ide.*vs code|switched.*vs code", re.I),
        "User Preferences",
        "preferred_ide",
        "VS Code",
        0.95,
        None,
    ),
    (
        re.compile(r"ai observability", re.I),
        "Project Information",
        "project",
        "AI Observability",
        0.85,
        None,
    ),
    (
        re.compile(r"long-term memory|long term memory engine", re.I),
        "Project Information",
        "project",
        "Long-Term Memory",
        0.95,
        None,
    ),
    (
        re.compile(r"legacybot", re.I),
        "Project Information",
        "project",
        "LegacyBot",
        0.7,
        None,
    ),
    (
        re.compile(r"prompt caching", re.I),
        "Project Information",
        "topic",
        "Prompt Caching",
        0.8,
        None,
    ),
    (
        re.compile(r"\brag\b|chunk size", re.I),
        "Project Information",
        "topic",
        "RAG",
        0.8,
        None,
    ),
    (
        re.compile(r"conversation summarization", re.I),
        "Project Information",
        "topic",
        "Conversation Summarization",
        0.8,
        None,
    ),
    (
        re.compile(r"kubernetes", re.I),
        "Technical Constraints",
        "deployment",
        "Kubernetes",
        0.8,
        None,
    ),
    (
        re.compile(r"unit test|pytest", re.I),
        "Technical Constraints",
        "testing",
        "Unit Testing",
        0.8,
        None,
    ),
    (
        re.compile(r"temporary.*debugging|ignore after 24h|temporary:", re.I),
        "Project Information",
        "temp_incident",
        "Temporary prod debugging",
        0.3,
        1,
    ),
]


def extract_from_conversation(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract memory records from one conversation.

    Returns list of memory dicts with category, key, value, confidence, metadata.
    """
    records: list[dict[str, Any]] = []
    conv_id = conversation["conversation_id"]

    for msg in conversation["messages"]:
        if msg["role"] != "user":
            continue
        text = msg["content"]
        for pattern, category, key, value, confidence, ttl in EXTRACTION_RULES:
            if pattern.search(text):
                records.append(
                    {
                        "memory_id": f"m_{conv_id}_{key}_{len(records)}",
                        "conversation_id": conv_id,
                        "category": category,
                        "key": key,
                        "value": value,
                        "confidence": confidence,
                        "ttl_days": ttl,
                        "text": text[:120],
                    }
                )
    return records


def extract_all(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract memories from all conversations — raw uncompressed list."""
    all_memories: list[dict[str, Any]] = []
    for conv in conversations:
        all_memories.extend(extract_from_conversation(conv))
    return all_memories
