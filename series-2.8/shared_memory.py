"""
Shared memory for Series 2.8 multi-agent orchestration.

Agents never communicate directly. They read and write structured keys:

  request, plan, architecture, database, backend, frontend,
  security, testing, devops, documentation, review, aggregated

Synchronization is orchestrator-managed (single writer per agent step).
"""

from __future__ import annotations

from typing import Any


class SharedMemory:
    """In-process shared context store for one orchestration run."""

    def __init__(self, request: dict[str, Any]) -> None:
        self._data: dict[str, Any] = {
            "request": {
                "request_id": request["request_id"],
                "prompt": request["prompt"],
                "category": request.get("category"),
                "complexity": request.get("complexity"),
                "security_level": request.get("security_level"),
            },
            "coding_standards": "Python 3.11+, type hints, pytest, OpenAPI 3.1",
            "security_rules": "OAuth2, RBAC, encrypt PII, audit all mutations",
        }
        self._history: list[dict[str, Any]] = []

    def read(self, key: str | None = None) -> Any:
        if key is None:
            return dict(self._data)
        return self._data.get(key)

    def write(self, key: str, value: Any, *, agent_id: str) -> None:
        self._data[key] = value
        self._history.append({"agent_id": agent_id, "key": key, "action": "write"})

    def snapshot(self) -> dict[str, Any]:
        """Read-only copy for agent context building."""
        return dict(self._data)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def has_domain_outputs(self, domains: tuple[str, ...]) -> bool:
        return all(d in self._data and self._data[d] for d in domains)

    def write_agent_output(self, agent_result: dict[str, Any]) -> None:
        """Store agent deliverable under its domain key."""
        domain = agent_result.get("domain", agent_result["agent_id"])
        self.write(domain, {
            "agent_id": agent_result["agent_id"],
            "summary": agent_result["output_text"][:500],
            "full_text": agent_result["output_text"],
            "quality_factor": agent_result.get("quality_factor", 0.8),
        }, agent_id=agent_result["agent_id"])

    def aggregate(self) -> str:
        """Result aggregator — merge domain outputs into unified solution."""
        parts = [
            f"# Unified Solution: {self._data['request']['prompt']}",
            "",
        ]
        for key in (
            "architecture", "database", "backend", "frontend",
            "security", "testing", "devops", "documentation",
        ):
            block = self._data.get(key)
            if block:
                parts.append(f"## {key.title()}")
                parts.append(block.get("summary", "")[:400])
                parts.append("")
        if self._data.get("review"):
            parts.append("## Review")
            parts.append(str(self._data["review"].get("summary", "")))
        return "\n".join(parts)

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)
