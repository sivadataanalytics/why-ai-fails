"""
Synthetic memory dataset for Series 2.6 (~100,000 records).

Categories:
  User Profile, Organization Policies, Project Knowledge, Coding Preferences,
  Security Standards, Database Preferences, Previous Decisions

Intentionally includes:
  - duplicate memories (same fact, many copies)
  - unrelated memories (noise)
  - obsolete memories (superseded frameworks)
  - conflicting memories (MySQL vs PostgreSQL — PostgreSQL wins on recency)
"""

from __future__ import annotations

import math
import random
from typing import Any

MEMORY_COUNT = 100_000
RANDOM_SEED = 42

# Global expected facts for evaluation (evaluator.py)
EXPECTED_MEMORIES = [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Secure Coding",
    "AI Observability",
]

# Canonical ground-truth memories — one logical fact each (used for precision/recall)
CANONICAL_TEMPLATES: list[dict[str, Any]] = [
    {
        "category": "User Profile",
        "key": "preferred_language",
        "value": "Python",
        "text": "Preferred Language: Python",
        "tags": ["python", "language"],
        "business_priority": 1.0,
    },
    {
        "category": "User Profile",
        "key": "preferred_framework",
        "value": "FastAPI",
        "text": "Framework: FastAPI for REST APIs",
        "tags": ["fastapi", "framework", "rest", "api"],
        "business_priority": 1.0,
    },
    {
        "category": "Database Preferences",
        "key": "database",
        "value": "PostgreSQL",
        "text": "Database: PostgreSQL for persistence",
        "tags": ["postgresql", "postgres", "database", "schema"],
        "business_priority": 0.95,
    },
    {
        "category": "Security Standards",
        "key": "secure_coding",
        "value": "Secure Coding",
        "text": "Security: Never store credentials in code — secure coding required",
        "tags": ["secure", "security", "authentication", "credentials"],
        "business_priority": 1.0,
    },
    {
        "category": "Project Knowledge",
        "key": "current_project",
        "value": "AI Observability",
        "text": "Current Project: AI Observability platform",
        "tags": ["observability", "ai", "project", "summarize"],
        "business_priority": 0.9,
    },
    {
        "category": "Coding Preferences",
        "key": "coding_style",
        "value": "Readable Python",
        "text": "Coding Style: Readable Python with type hints",
        "tags": ["python", "readable", "code", "style"],
        "business_priority": 0.85,
    },
]

# Noise templates — unrelated enterprise memories
NOISE_TEMPLATES: list[dict[str, Any]] = [
    {"category": "Project Knowledge", "key": "project", "value": "Legacy CRM Migration", "tags": ["crm"]},
    {"category": "Project Knowledge", "key": "project", "value": "Mobile App Redesign", "tags": ["mobile"]},
    {"category": "User Profile", "key": "preferred_language", "value": "JavaScript", "tags": ["javascript"]},
    {"category": "User Profile", "key": "preferred_framework", "value": "Django", "tags": ["django"]},
    {"category": "Database Preferences", "key": "database", "value": "MongoDB", "tags": ["mongodb"]},
    {"category": "Organization Policies", "key": "policy", "value": "Weekly standup mandatory", "tags": ["standup"]},
    {"category": "Previous Decisions", "key": "decision", "value": "Use Redis for caching", "tags": ["redis"]},
    {"category": "Security Standards", "key": "compliance", "value": "SOC2 audit Q3", "tags": ["soc2"]},
    {"category": "Coding Preferences", "key": "linting", "value": "ESLint strict mode", "tags": ["eslint"]},
    {"category": "Project Knowledge", "key": "project", "value": "Kubernetes cluster upgrade", "tags": ["kubernetes"]},
]

# Obsolete / conflicting entries
OBSOLETE_TEMPLATES: list[dict[str, Any]] = [
    {"category": "User Profile", "key": "preferred_framework", "value": "Flask", "tags": ["flask"], "obsolete": True},
    {"category": "Database Preferences", "key": "database", "value": "MySQL", "tags": ["mysql"], "obsolete": True},
    {"category": "User Profile", "key": "preferred_ide", "value": "PyCharm", "tags": ["pycharm"], "obsolete": True},
]


def _build_record(
    idx: int,
    template: dict[str, Any],
    *,
    canonical: bool,
    recency: float,
    confidence: float,
) -> dict[str, Any]:
    """Materialize one memory record from a template."""
    text = template.get("text") or f"{template['key']}: {template['value']}"
    return {
        "memory_id": f"mem_{idx:06d}",
        "category": template["category"],
        "key": template["key"],
        "value": template["value"],
        "text": text,
        "tags": list(template.get("tags", [])),
        "confidence": round(confidence, 3),
        "recency": round(recency, 3),
        "frequency": random.randint(1, 50),
        "business_priority": template.get("business_priority", 0.5),
        "canonical": canonical,
        "obsolete": template.get("obsolete", False),
    }


def generate_memories(count: int = MEMORY_COUNT) -> list[dict[str, Any]]:
    """
    Build `count` memory records with controlled duplicates and noise.

    Distribution (~100k):
      - ~15k duplicates of canonical facts
      - ~2k obsolete/conflicting
      - ~83k unrelated noise
    """
    random.seed(RANDOM_SEED)
    memories: list[dict[str, Any]] = []
    idx = 0

    # Canonical facts + duplicates (~15% of store)
    duplicate_target = int(count * 0.15)
    while len(memories) < duplicate_target:
        for tmpl in CANONICAL_TEMPLATES:
            if len(memories) >= duplicate_target:
                break
            idx += 1
            recency = random.uniform(0.6, 1.0)
            confidence = random.uniform(0.85, 0.99)
            memories.append(
                _build_record(idx, tmpl, canonical=(idx % 50 == 0), recency=recency, confidence=confidence)
            )

    # Obsolete / conflicting (~2%)
    obsolete_target = int(count * 0.02)
    while len(memories) < duplicate_target + obsolete_target:
        tmpl = random.choice(OBSOLETE_TEMPLATES)
        idx += 1
        memories.append(
            _build_record(idx, tmpl, canonical=False, recency=random.uniform(0.1, 0.4), confidence=0.6)
        )

    # Unrelated noise (remainder)
    while len(memories) < count:
        tmpl = random.choice(NOISE_TEMPLATES)
        idx += 1
        memories.append(
            _build_record(
                idx,
                tmpl,
                canonical=False,
                recency=random.uniform(0.2, 0.8),
                confidence=random.uniform(0.4, 0.8),
            )
        )

    return memories
