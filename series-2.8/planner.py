"""
Task decomposition for Series 2.8.

Planner Agent breaks enterprise requests into dependent tasks assigned to
specialized agents. Pure Python — no LLM required for dry-run.
"""

from __future__ import annotations

from typing import Any

from agents import EXECUTION_AGENTS
from tasks import REQUIRED_DOMAINS

# Task graph: agent_id → depends on agent_ids (must complete first)
TASK_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "architecture": (),
    "database": ("architecture",),
    "backend": ("architecture", "database"),
    "frontend": ("architecture", "backend"),
    "security": ("architecture", "backend"),
    "testing": ("backend", "frontend"),
    "devops": ("backend", "testing"),
    "documentation": ("architecture", "backend", "frontend", "database", "security", "testing", "devops"),
}


def decompose_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Planner output: ordered task list with agent assignment and dependencies.

    Full-stack enterprise builds always include all execution domains.
    """
    domains = request.get("required_domains") or list(REQUIRED_DOMAINS)
    tasks: list[dict[str, Any]] = []
    for i, agent_id in enumerate(domains, start=1):
        if agent_id not in EXECUTION_AGENTS:
            continue
        deps = TASK_DEPENDENCIES.get(agent_id, ())
        tasks.append({
            "task_id": f"t{i:02d}",
            "agent_id": agent_id,
            "title": _task_title(agent_id, request),
            "depends_on": list(deps),
            "priority": i,
        })
    return tasks


def plan_request(request: dict[str, Any]) -> dict[str, Any]:
    """Full planner phase — task list + planning artifact for shared memory."""
    tasks = decompose_request(request)
    plan_text = _format_plan(request, tasks)
    return {
        "agent_id": "planner",
        "tasks": tasks,
        "task_count": len(tasks),
        "plan_text": plan_text,
        "critical_path": _critical_path(tasks),
    }


def _task_title(agent_id: str, request: dict[str, Any]) -> str:
    category = request.get("category", "enterprise").replace("_", " ")
    titles = {
        "architecture": f"Design {category} system architecture",
        "backend": f"Implement {category} backend APIs",
        "frontend": f"Build {category} UI components",
        "database": f"Define {category} database schema",
        "security": f"Apply security controls for {category}",
        "testing": f"Author tests for {category} platform",
        "devops": f"Create deployment pipeline for {category}",
        "documentation": f"Write documentation for {category} platform",
    }
    return titles.get(agent_id, f"Execute {agent_id} work")


def _format_plan(request: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    lines = [
        f"Plan for: {request['prompt']}",
        f"Category: {request.get('category', 'general')}",
        f"Tasks: {len(tasks)}",
        "",
        "Task graph:",
    ]
    for t in tasks:
        dep = ", ".join(t["depends_on"]) if t["depends_on"] else "(none)"
        lines.append(f"  {t['task_id']} [{t['agent_id']}] depends on: {dep}")
    return "\n".join(lines)


def _critical_path(tasks: list[dict[str, Any]]) -> list[str]:
    """Longest dependency chain — used for latency estimation."""
    by_agent = {t["agent_id"]: t for t in tasks}
    memo: dict[str, list[str]] = {}

    def path(agent_id: str) -> list[str]:
        if agent_id in memo:
            return memo[agent_id]
        task = by_agent.get(agent_id)
        if not task or not task["depends_on"]:
            memo[agent_id] = [agent_id]
            return memo[agent_id]
        best: list[str] = []
        for dep in task["depends_on"]:
            candidate = path(dep) + [agent_id]
            if len(candidate) > len(best):
                best = candidate
        memo[agent_id] = best or [agent_id]
        return memo[agent_id]

    longest: list[str] = []
    for t in tasks:
        p = path(t["agent_id"])
        if len(p) > len(longest):
            longest = p
    return longest
