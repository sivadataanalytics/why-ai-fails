"""
Execution scheduler for Series 2.8.

Supports:
  sequential — tasks run one after another (respecting dependencies)
  parallel   — independent tasks grouped into waves; wave runs concurrently

Scheduler understands the task dependency graph from planner.py.
"""

from __future__ import annotations

from typing import Any


def schedule_sequential(tasks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """
    One task per wave — total order respecting dependencies.

    Returns list of waves; each wave is a list of tasks to run (size 1).
    """
    ordered = _topological_sort(tasks)
    return [[t] for t in ordered]


def schedule_parallel(tasks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """
    Group tasks into parallel waves.

    Wave N contains all tasks whose dependencies are satisfied by prior waves.
    """
    waves: list[list[dict[str, Any]]] = []
    remaining = list(tasks)
    completed: set[str] = set()

    while remaining:
        ready = [
            t for t in remaining
            if all(dep in completed for dep in t.get("depends_on", []))
        ]
        if not ready:
            # Cycle or missing dep — fallback to sequential remainder
            ready = [remaining[0]]
        waves.append(ready)
        for t in ready:
            completed.add(t["agent_id"])
            remaining.remove(t)
    return waves


def schedule(tasks: list[dict[str, Any]], *, mode: str) -> list[list[dict[str, Any]]]:
    if mode == "parallel":
        return schedule_parallel(tasks)
    return schedule_sequential(tasks)


def wave_latency_seconds(wave: list[dict[str, Any]], agent_latencies: dict[str, float]) -> float:
    """Parallel wave latency = max agent latency in the wave."""
    if not wave:
        return 0.0
    return max(agent_latencies.get(t["agent_id"], 1.0) for t in wave)


def total_scheduled_latency(
    waves: list[list[dict[str, Any]]],
    agent_latencies: dict[str, float],
    *,
    overhead_per_wave: float = 0.15,
) -> float:
    """Sum of wave latencies + small orchestration overhead per wave."""
    total = 0.0
    for wave in waves:
        total += wave_latency_seconds(wave, agent_latencies) + overhead_per_wave
    return round(total, 2)


def _topological_sort(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {t["agent_id"]: t for t in tasks}
    visited: set[str] = set()
    result: list[dict[str, Any]] = []

    def visit(agent_id: str) -> None:
        if agent_id in visited or agent_id not in by_id:
            return
        visited.add(agent_id)
        for dep in by_id[agent_id].get("depends_on", []):
            visit(dep)
        result.append(by_id[agent_id])

    for t in tasks:
        visit(t["agent_id"])
    return result
