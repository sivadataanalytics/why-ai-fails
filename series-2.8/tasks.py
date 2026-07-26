"""
Synthetic enterprise software requests for Series 2.8 (~500 requests).

Each request requires multiple specialized agents (architecture, backend,
frontend, database, security, testing, deployment, documentation).

Categories: Banking, Healthcare, Retail, Observability, CRM, AI Platform,
Ecommerce, Kubernetes.
"""

from __future__ import annotations

import random
from typing import Any

REQUEST_COUNT = 500
RANDOM_SEED = 42

DEFAULT_REQUEST_ID = "r0024"

CATEGORIES = (
    "banking",
    "healthcare",
    "retail",
    "observability",
    "crm",
    "ai_platform",
    "ecommerce",
    "kubernetes",
)

# Required agent domains per full-stack enterprise build
REQUIRED_DOMAINS = (
    "architecture",
    "backend",
    "frontend",
    "database",
    "security",
    "testing",
    "devops",
    "documentation",
)

CATEGORY_TEMPLATES: dict[str, list[str]] = {
    "banking": [
        "Build a production-ready {focus} banking application with secure transactions.",
        "Design and implement a {focus} core banking platform for retail customers.",
        "Create a compliant {focus} banking system with audit trails and reporting.",
    ],
    "healthcare": [
        "Build a production-ready {focus} patient management platform.",
        "Design a HIPAA-compliant {focus} healthcare portal with scheduling.",
        "Implement a {focus} clinical workflow system for hospital staff.",
    ],
    "retail": [
        "Build a production-ready {focus} retail inventory and POS system.",
        "Design a {focus} omnichannel retail platform with real-time stock.",
        "Create a {focus} store operations dashboard for regional managers.",
    ],
    "observability": [
        "Build a production-ready {focus} observability platform for microservices.",
        "Design a {focus} metrics and tracing system for Kubernetes workloads.",
        "Implement a {focus} SRE incident management and alerting platform.",
    ],
    "crm": [
        "Build a production-ready {focus} CRM for enterprise sales teams.",
        "Design a {focus} customer engagement platform with pipeline analytics.",
        "Create a {focus} support and ticketing CRM with SLA tracking.",
    ],
    "ai_platform": [
        "Build a production-ready {focus} AI agent orchestration platform.",
        "Design a {focus} LLM gateway with routing, caching, and observability.",
        "Implement a {focus} enterprise RAG platform with governance controls.",
    ],
    "ecommerce": [
        "Build a production-ready {focus} ecommerce marketplace.",
        "Design a {focus} checkout and payments platform with fraud detection.",
        "Create a {focus} product catalog and recommendation engine.",
    ],
    "kubernetes": [
        "Build a production-ready {focus} Kubernetes deployment platform.",
        "Design a {focus} GitOps pipeline for multi-cluster applications.",
        "Implement a {focus} platform engineering portal with self-service namespaces.",
    ],
}

FOCUS_TERMS = (
    "cloud-native",
    "multi-tenant",
    "high-availability",
    "event-driven",
    "real-time",
    "regulated",
    "global-scale",
    "zero-trust",
)


def _make_request(index: int, category: str) -> dict[str, Any]:
    templates = CATEGORY_TEMPLATES[category]
    focus = FOCUS_TERMS[index % len(FOCUS_TERMS)]
    prompt = templates[index % len(templates)].format(focus=focus)
    complexity = "complex" if index % 5 == 0 else "medium"
    return {
        "request_id": f"r{index:04d}",
        "category": category,
        "prompt": prompt,
        "complexity": complexity,
        "required_domains": list(REQUIRED_DOMAINS),
        "security_level": "restricted" if category in ("banking", "healthcare") else "internal",
    }


def generate_requests(count: int = REQUEST_COUNT) -> list[dict[str, Any]]:
    """Generate deterministic enterprise request dataset."""
    rng = random.Random(RANDOM_SEED)
    requests: list[dict[str, Any]] = []
    per_category = max(1, count // len(CATEGORIES))
    idx = 1
    for category in CATEGORIES:
        for _ in range(per_category):
            if idx > count:
                break
            requests.append(_make_request(idx, category))
            idx += 1
    while len(requests) < count:
        category = CATEGORIES[len(requests) % len(CATEGORIES)]
        requests.append(_make_request(len(requests) + 1, category))
    rng.shuffle(requests)
    # Re-assign sequential IDs after shuffle for stable lookup
    for i, req in enumerate(requests, start=1):
        req["request_id"] = f"r{i:04d}"
    return requests


REQUESTS: list[dict[str, Any]] = generate_requests()
REQUESTS_BY_ID: dict[str, dict[str, Any]] = {r["request_id"]: r for r in REQUESTS}

# Canonical demo request from lab spec
DEMO_PROMPT = "Build a production-ready banking application."
