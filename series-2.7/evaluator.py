"""
Evaluation metrics for Series 2.7 model routing lab.

Accuracy           — response quality for selected model / task pairing
Model Utilization  — % of requests per model
Escalation Rate    — confidence strategy escalations
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from models import get_model, model_supports_task


def _result_quality(result: dict[str, Any]) -> float:
    """
    Simulated response quality (0–1) for model + task pairing.

    Single-model baseline always scores high (large general handles all tasks).
    Smart routing scores high when model matches task; penalizes mismatches.
    """
    model_id = result["model_id"]
    task_type = result.get("task_type", "")
    expected = result.get("expected_model", "")
    quality = get_model(model_id)["quality_score"]

    if model_id == "large_general":
        return round(quality, 2)

    if model_id == expected:
        return round(quality, 2)

    if {model_id, expected} <= {"medium_coding", "medium_coding_internal"}:
        return round(min(0.98, quality * 0.98), 2)

    if model_supports_task(model_id, task_type):
        return round(min(0.97, quality * 0.95), 2)

    return round(quality * 0.52, 2)


def routing_accuracy(results: list[dict[str, Any]]) -> float:
    """Mean simulated response quality across routed requests."""
    if not results:
        return 0.0
    scores = [_result_quality(r) for r in results]
    return round(sum(scores) / len(scores), 2)


def routing_match_rate(results: list[dict[str, Any]]) -> float:
    """Fraction routed to exactly the expected model ID."""
    if not results:
        return 0.0
    hits = sum(1 for r in results if r["model_id"] == r["expected_model"]
               or {r["model_id"], r["expected_model"]} <= {"medium_coding", "medium_coding_internal"})
    return round(hits / len(results), 2)


def model_utilization(results: list[dict[str, Any]]) -> dict[str, float]:
    """Percentage of requests handled by each model."""
    if not results:
        return {}
    counts = Counter(r["model_id"] for r in results)
    total = len(results)
    return {mid: round(100 * count / total, 1) for mid, count in sorted(counts.items())}


def escalation_rate(results: list[dict[str, Any]]) -> float:
    """Share of requests that escalated (confidence routing)."""
    if not results:
        return 0.0
    escalated = sum(1 for r in results if r.get("escalated"))
    return round(escalated / len(results), 2)


def aggregate_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize benchmark run across all requests."""
    n = len(results)
    if n == 0:
        return {}

    return {
        "request_count": n,
        "accuracy": routing_accuracy(results),
        "routing_match_rate": routing_match_rate(results),
        "avg_prompt_tokens": round(sum(r["prompt_tokens"] for r in results) / n, 1),
        "avg_completion_tokens": round(sum(r["completion_tokens"] for r in results) / n, 1),
        "avg_total_tokens": round(sum(r["total_tokens"] for r in results) / n, 1),
        "avg_latency_seconds": round(sum(r["latency_seconds"] for r in results) / n, 2),
        "avg_cost": round(sum(r["estimated_cost"] for r in results) / n, 4),
        "total_cost": round(sum(r["estimated_cost"] for r in results), 4),
        "model_utilization": model_utilization(results),
        "escalation_rate": escalation_rate(results),
    }
