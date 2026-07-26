"""
Synthetic AI request dataset for Series 2.7 (~1,000 requests).

Each record includes prompt, expected complexity, task type, security level, and ideal model.
"""

from __future__ import annotations

import random
from typing import Any

REQUEST_COUNT = 1000
RANDOM_SEED = 42

TASK_TYPES = (
    "translation",
    "email_summarization",
    "classification",
    "sql_generation",
    "backend_api",
    "architecture_design",
    "code_review",
    "legal_analysis",
    "vision",
    "reasoning",
)

COMPLEXITIES = ("simple", "medium", "complex")

SECURITY_LEVELS = ("public", "internal", "restricted")

# Ground-truth routing targets
TASK_TO_MODEL: dict[str, str] = {
    "translation": "small",
    "email_summarization": "small",
    "classification": "small",
    "sql_generation": "medium_coding",
    "backend_api": "medium_coding",
    "code_review": "medium_coding",
    "architecture_design": "large_reasoning",
    "legal_analysis": "large_reasoning",
    "reasoning": "large_reasoning",
    "vision": "vision",
}

COMPLEXITY_BY_TASK: dict[str, str] = {
    "translation": "simple",
    "email_summarization": "simple",
    "classification": "simple",
    "sql_generation": "medium",
    "backend_api": "medium",
    "code_review": "medium",
    "vision": "medium",
    "architecture_design": "complex",
    "legal_analysis": "complex",
    "reasoning": "complex",
}

PROMPT_TEMPLATES: dict[str, list[str]] = {
    "translation": [
        "Translate to Spanish: Hello, how are you today?",
        "Translate this paragraph to French: Our deployment completed successfully.",
        "Convert the following text to German: Please review the attached invoice.",
    ],
    "email_summarization": [
        "Summarize this email thread about the Q3 budget review.",
        "Provide a short summary of the customer escalation email chain.",
        "Summarize the meeting follow-up email in three bullet points.",
    ],
    "classification": [
        "Classify sentiment: The product launch exceeded expectations.",
        "Is this support ticket urgent or normal priority?",
        "Label this feedback as positive, neutral, or negative.",
    ],
    "sql_generation": [
        "Generate SQL to list active users created in the last 30 days.",
        "Write a PostgreSQL query joining orders and customers by region.",
        "Create SQL to find duplicate email addresses in the users table.",
    ],
    "backend_api": [
        "Generate a secure FastAPI REST API for user profiles.",
        "Create Python endpoints for order management with pagination.",
        "Build a Flask API handler for webhook verification.",
    ],
    "architecture_design": [
        "Design Kubernetes architecture for a multi-tenant observability platform.",
        "Propose a microservices architecture for real-time fraud detection.",
        "Design a scalable event-driven system for IoT telemetry ingestion.",
    ],
    "code_review": [
        "Review this Python function for security and performance issues.",
        "Identify bugs in the attached authentication middleware code.",
        "Suggest improvements for the database connection pooling module.",
    ],
    "legal_analysis": [
        "Analyze contractual liability clauses in this SaaS agreement excerpt.",
        "Summarize GDPR implications for cross-border data transfer.",
        "Review indemnification terms in the vendor MSA draft.",
    ],
    "vision": [
        "Describe defects visible in this manufacturing line image.",
        "Extract text and layout from the scanned invoice image.",
        "Identify safety violations in the warehouse photo.",
    ],
    "reasoning": [
        "Explain why throughput dropped after the cache cluster upgrade.",
        "Determine root cause from these conflicting incident timelines.",
        "Evaluate trade-offs between strong consistency and availability.",
    ],
}


def _security_for_task(task_type: str, rng: random.Random) -> str:
    coding_tasks = {"sql_generation", "backend_api", "code_review", "architecture_design"}
    if task_type in coding_tasks:
        roll = rng.random()
        if roll < 0.15:
            return "restricted"
        if roll < 0.35:
            return "internal"
    return rng.choices(SECURITY_LEVELS, weights=[0.72, 0.20, 0.08], k=1)[0]


def _expected_model(task_type: str, security: str) -> str:
    base = TASK_TO_MODEL[task_type]
    if security == "restricted" and base == "medium_coding":
        return "medium_coding_internal"
    return base


def _context_tokens(task_type: str, complexity: str, rng: random.Random) -> int:
    base = {"simple": 120, "medium": 280, "complex": 520}[complexity]
    if task_type in ("architecture_design", "legal_analysis", "vision"):
        base += 80
    return base + rng.randint(-30, 60)


def generate_requests(count: int = REQUEST_COUNT) -> list[dict[str, Any]]:
    """Materialize synthetic request dataset with reproducible seed."""
    rng = random.Random(RANDOM_SEED)
    requests: list[dict[str, Any]] = []

    for i in range(count):
        task_type = TASK_TYPES[i % len(TASK_TYPES)] if i < len(TASK_TYPES) else rng.choice(TASK_TYPES)
        complexity = COMPLEXITY_BY_TASK[task_type]
        security = _security_for_task(task_type, rng)
        templates = PROMPT_TEMPLATES[task_type]
        prompt = templates[i % len(templates)]
        if i >= len(TASK_TYPES):
            prompt = f"{prompt} (request variant {i})"

        expected_model = _expected_model(task_type, security)
        requests.append({
            "request_id": f"r{i + 1:04d}",
            "prompt": prompt,
            "task_type": task_type,
            "complexity": complexity,
            "security_level": security,
            "expected_model": expected_model,
            "context_tokens": _context_tokens(task_type, complexity, rng),
        })

    return requests


REQUESTS = generate_requests()
REQUESTS_BY_ID = {r["request_id"]: r for r in REQUESTS}
DEFAULT_REQUEST_ID = "r0001"
