"""
Specialized agent pool for Series 2.8 multi-agent orchestration.

Agents never communicate directly — they read and write SharedMemory only.

Agent roles:
  planner, architecture, backend, frontend, database, security,
  testing, devops, documentation, reviewer
"""

from __future__ import annotations

from typing import Any

from common.token_usage import estimate_tokens

# Agent metadata: domain, typical output size, base latency (seconds, dry-run)
AGENTS: dict[str, dict[str, Any]] = {
    "planner": {
        "name": "Planner Agent",
        "domain": "planning",
        "description": "Understand request, decompose tasks, estimate dependencies",
        "base_latency": 0.4,
        "output_tokens": 180,
        "prompt_overhead": 120,
    },
    "architecture": {
        "name": "Architecture Agent",
        "domain": "architecture",
        "description": "System design, API boundaries, component diagram",
        "base_latency": 1.2,
        "output_tokens": 420,
        "prompt_overhead": 200,
    },
    "backend": {
        "name": "Backend Agent",
        "domain": "backend",
        "description": "REST APIs, business logic, validation",
        "base_latency": 1.4,
        "output_tokens": 520,
        "prompt_overhead": 250,
    },
    "frontend": {
        "name": "Frontend Agent",
        "domain": "frontend",
        "description": "UI components and screens",
        "base_latency": 1.1,
        "output_tokens": 380,
        "prompt_overhead": 220,
    },
    "database": {
        "name": "Database Agent",
        "domain": "database",
        "description": "Schema, indexes, SQL",
        "base_latency": 0.9,
        "output_tokens": 340,
        "prompt_overhead": 180,
    },
    "security": {
        "name": "Security Agent",
        "domain": "security",
        "description": "Authentication, authorization, vulnerability review",
        "base_latency": 1.0,
        "output_tokens": 300,
        "prompt_overhead": 200,
    },
    "testing": {
        "name": "Testing Agent",
        "domain": "testing",
        "description": "Unit and integration tests",
        "base_latency": 0.8,
        "output_tokens": 280,
        "prompt_overhead": 190,
    },
    "devops": {
        "name": "DevOps Agent",
        "domain": "devops",
        "description": "Docker, Kubernetes, CI/CD",
        "base_latency": 1.0,
        "output_tokens": 320,
        "prompt_overhead": 200,
    },
    "documentation": {
        "name": "Documentation Agent",
        "domain": "documentation",
        "description": "README and API documentation",
        "base_latency": 0.6,
        "output_tokens": 220,
        "prompt_overhead": 160,
    },
    "reviewer": {
        "name": "Reviewer Agent",
        "domain": "reviewer",
        "description": "Consistency, missing components, final validation",
        "base_latency": 0.8,
        "output_tokens": 200,
        "prompt_overhead": 350,
    },
}

SINGLE_AGENT_ID = "single_general"
SINGLE_AGENT = {
    "name": "Single General Agent",
    "domain": "general",
    "base_latency": 18.4,
    "output_tokens": 900,
    "prompt_overhead": 400,
}

EXECUTION_AGENTS = (
    "architecture",
    "backend",
    "frontend",
    "database",
    "security",
    "testing",
    "devops",
    "documentation",
)


def get_agent(agent_id: str) -> dict[str, Any]:
    if agent_id == SINGLE_AGENT_ID:
        return SINGLE_AGENT
    return AGENTS[agent_id]


def simulate_agent_output(agent_id: str, request: dict[str, Any], memory_snapshot: dict[str, Any]) -> dict[str, Any]:
    """
    Produce deterministic simulated output for dry-run (no Gemini).

    Quality improves when agent reads relevant prior outputs from shared memory.
    """
    agent = get_agent(agent_id)
    domain = agent.get("domain", agent_id)
    category = request.get("category", "general")

    # Check if dependencies exist in memory for consistency bonus
    deps_present = _dependency_coverage(domain, memory_snapshot)
    quality_factor = 0.72 + 0.28 * deps_present

    title = f"{category.replace('_', ' ').title()} — {agent['name']} deliverable"
    summary = (
        f"Completed {domain} work for: {request['prompt'][:80]}… "
        f"(deps satisfied: {deps_present:.0%})"
    )
    body = _template_body(agent_id, category)

    output_text = f"# {title}\n\n{summary}\n\n{body}"
    prompt_text = f"Request: {request['prompt']}\nMemory keys: {list(memory_snapshot.keys())}"
    prompt_tokens = estimate_tokens(prompt_text) + agent.get("prompt_overhead", 150)
    completion_tokens = agent.get("output_tokens", 200)

    return {
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "domain": domain,
        "output_text": output_text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": round(agent.get("base_latency", 1.0), 2),
        "quality_factor": round(quality_factor, 2),
        "deps_coverage": deps_present,
    }


def _dependency_coverage(domain: str, memory: dict[str, Any]) -> float:
    """Fraction of expected upstream memory keys present before this agent runs."""
    needs: dict[str, tuple[str, ...]] = {
        "architecture": ("request",),
        "database": ("request", "architecture"),
        "backend": ("request", "architecture", "database"),
        "frontend": ("request", "architecture", "backend"),
        "security": ("request", "architecture", "backend"),
        "testing": ("request", "backend", "frontend"),
        "devops": ("request", "backend", "testing"),
        "documentation": ("request", "architecture", "backend", "frontend", "database"),
        "planning": ("request",),
        "reviewer": ("request",),
        "general": ("request",),
    }
    required = needs.get(domain, ("request",))
    if not required:
        return 1.0
    hits = sum(1 for k in required if k in memory and memory[k])
    return hits / len(required)


def _template_body(agent_id: str, category: str) -> str:
    bodies = {
        "architecture": "- API gateway + service boundaries\n- Event bus for async workflows\n- Component diagram attached",
        "backend": "- REST endpoints with validation\n- Domain services and repository layer\n- OpenAPI spec draft",
        "frontend": "- Dashboard shell and navigation\n- Key screens for primary workflows\n- Component library baseline",
        "database": "- Normalized schema with audit tables\n- Indexes for hot query paths\n- Migration scripts",
        "security": "- OAuth2 + RBAC model\n- Encryption at rest and in transit\n- Threat model for {cat}",
        "testing": "- Unit tests for core services\n- Integration tests for API flows\n- CI test gate defined",
        "devops": "- Dockerfile multi-stage build\n- Kubernetes manifests + HPA\n- GitHub Actions pipeline",
        "documentation": "- README with setup steps\n- API reference from OpenAPI\n- Runbook for on-call",
        "planning": "- Task graph with dependencies\n- Work breakdown by agent domain\n- Critical path identified",
    }
    text = bodies.get(agent_id, f"- Deliverable for {category}")
    return text.replace("{cat}", category.replace("_", " "))
