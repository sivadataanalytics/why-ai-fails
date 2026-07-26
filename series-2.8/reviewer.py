"""
Reviewer agent for Series 2.8.

Validates aggregated outputs for:
  - Architecture consistency
  - Missing tasks / domains
  - Security coverage
  - Broken dependencies

Supports one review iteration — failed domains can be re-run once.
"""

from __future__ import annotations

from typing import Any

from agents import EXECUTION_AGENTS, simulate_agent_output
from shared_memory import SharedMemory
from tasks import REQUIRED_DOMAINS


def review(memory: SharedMemory, *, request: dict[str, Any]) -> dict[str, Any]:
    """
    Run reviewer pass on shared memory. Returns review result + optional rework list.
    """
    missing = _missing_domains(memory)
    conflicts = _detect_conflicts(memory)
    security_gaps = _security_gaps(memory, request)

    issues = missing + conflicts + security_gaps
    passed = len(issues) == 0

    base_score = 0.88 if passed else max(0.55, 0.88 - 0.08 * len(issues))
    consistency = _consistency_score(memory)
    security_score = 0.95 if not security_gaps else 0.72

    review_score = round((base_score + consistency + security_score) / 3, 2)

    rework_agents = _rework_agents(missing, conflicts, max_rework=2)

    summary = (
        f"Review {'PASSED' if passed else 'NEEDS REWORK'} — "
        f"{len(issues)} issue(s), score={review_score}"
    )
    detail = {
        "passed": passed,
        "issues": issues,
        "review_score": review_score,
        "consistency_score": consistency,
        "security_score": security_score,
        "rework_agents": rework_agents,
        "summary": summary,
    }
    memory.write("review", detail, agent_id="reviewer")
    return detail


def apply_rework(
    memory: SharedMemory,
    request: dict[str, Any],
    rework_agents: list[str],
) -> list[dict[str, Any]]:
    """One review iteration — re-run flagged agents and update memory."""
    results: list[dict[str, Any]] = []
    for agent_id in rework_agents:
        result = simulate_agent_output(agent_id, request, memory.snapshot())
        # Rework pass gets quality boost (reviewer feedback applied)
        result["quality_factor"] = min(0.98, result["quality_factor"] + 0.12)
        result["rework"] = True
        memory.write_agent_output(result)
        results.append(result)
    return results


def _missing_domains(memory: SharedMemory) -> list[str]:
    missing = []
    for domain in REQUIRED_DOMAINS:
        if domain not in memory.snapshot():
            missing.append(f"missing domain: {domain}")
    return missing


def _detect_conflicts(memory: SharedMemory) -> list[str]:
    issues: list[str] = []
    snap = memory.snapshot()
    backend = snap.get("backend")
    frontend = snap.get("frontend")
    if backend and frontend:
        bq = backend.get("quality_factor", 1)
        fq = frontend.get("quality_factor", 1)
        if bq < 0.75 and fq > 0.85:
            issues.append("conflict: frontend assumes APIs not yet stable in backend")
    arch = snap.get("architecture")
    db = snap.get("database")
    if arch and not db:
        issues.append("conflict: architecture defined but database schema missing")
    return issues


def _security_gaps(memory: SharedMemory, request: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    if request.get("security_level") in ("restricted", "internal"):
        sec = memory.read("security")
        if not sec:
            gaps.append("security: no security agent output for regulated request")
        elif sec.get("quality_factor", 0) < 0.7:
            gaps.append("security: security review quality below threshold")
    return gaps


def _consistency_score(memory: SharedMemory) -> float:
    snap = memory.snapshot()
    factors = [
        snap[d]["quality_factor"]
        for d in EXECUTION_AGENTS
        if d in snap and isinstance(snap[d], dict) and "quality_factor" in snap[d]
    ]
    if not factors:
        return 0.5
    avg = sum(factors) / len(factors)
    spread = max(factors) - min(factors)
    penalty = min(0.15, spread * 0.3)
    return round(max(0.5, avg - penalty), 2)


def _rework_agents(missing: list[str], conflicts: list[str], *, max_rework: int) -> list[str]:
    agents: list[str] = []
    for issue in missing + conflicts:
        for domain in REQUIRED_DOMAINS:
            if domain in issue and domain not in agents:
                agents.append(domain)
    return agents[:max_rework]
