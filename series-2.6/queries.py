"""
Benchmark queries for Series 2.6 memory retrieval lab.
"""

from __future__ import annotations

from typing import Any

QUERIES: list[dict[str, Any]] = [
    {
        "id": "q1",
        "query": "Generate a secure FastAPI REST API.",
        "expected_values": ["Python", "FastAPI", "Secure Coding"],
        "intent_keywords": ["secure", "fastapi", "rest", "api", "python"],
    },
    {
        "id": "q2",
        "query": "Generate Python code.",
        "expected_values": ["Python", "Readable Python"],
        "intent_keywords": ["python", "code", "readable"],
    },
    {
        "id": "q3",
        "query": "Create PostgreSQL schema.",
        "expected_values": ["PostgreSQL"],
        "intent_keywords": ["postgresql", "postgres", "schema", "database"],
    },
    {
        "id": "q4",
        "query": "Generate secure authentication.",
        "expected_values": ["Secure Coding", "Python"],
        "intent_keywords": ["secure", "authentication", "credentials"],
    },
    {
        "id": "q5",
        "query": "Summarize AI Observability project.",
        "expected_values": ["AI Observability"],
        "intent_keywords": ["observability", "ai", "project", "summarize"],
    },
]

QUERIES_BY_ID = {q["id"]: q for q in QUERIES}

DEFAULT_QUERY_ID = "q1"
