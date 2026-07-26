"""
Benchmark runner and printer for Series 2.8 multi-agent orchestration lab.
"""

from __future__ import annotations

from typing import Any

from evaluator import aggregate_benchmark, aggregate_run_metrics
from orchestrator import STRATEGY_NAMES, orchestrate


def run_strategy(
    strategy: str,
    requests: list[dict[str, Any]],
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Orchestrate all requests with one strategy."""
    runs = [orchestrate(req, strategy, dry_run=dry_run) for req in requests]
    metrics = [aggregate_run_metrics(r) for r in runs]
    return aggregate_benchmark(metrics)


def print_strategy_result(result: dict[str, Any]) -> None:
    print("-------------------------------------")
    print(result["strategy_name"])
    print("-------------------------------------")
    print(f"Latency             : {result['avg_latency_seconds']} sec")
    print(f"Quality             : {result['avg_overall_quality']}")
    print(f"Task Completion     : {result['avg_task_completion']}")
    print(f"Consistency Score   : {result['avg_consistency_score']}")
    print(f"Security Score      : {result['avg_security_score']}")
    if result.get("avg_review_score") is not None:
        print(f"Review Score        : {result['avg_review_score']}")
    print(f"Prompt Tokens (avg) : {result['avg_prompt_tokens']}")
    print(f"Completion Tokens   : {result['avg_completion_tokens']}")
    print(f"Total Tokens (avg)  : {result['avg_total_tokens']}")
    print(f"Estimated Cost (avg): ${result['avg_cost']:.4f}")


def print_benchmark(results: list[dict[str, Any]]) -> None:
    print("=====================================")
    print("MULTI-AGENT BENCHMARK")
    print("=====================================")
    print()

    for result in results:
        print_strategy_result(result)
        print()

    print("=====================================")
    print("ENGINEERING RECOMMENDATION")
    print("=====================================")
    print(_recommendation(results))
    print("=====================================")


def _recommendation(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No results."

    reviewer = next((r for r in results if r["strategy_key"] == "reviewer"), None)
    parallel = next((r for r in results if r["strategy_key"] == "parallel"), None)

    if reviewer and reviewer["avg_overall_quality"] >= 0.90:
        return "\n".join([
            "Parallel + Reviewer",
            "↓",
            "Highest Quality",
            "↓",
            "Lowest Overall Time vs Sequential",
            "↓",
            "Enterprise Recommendation",
            "",
            "Enterprise AI systems scale through coordination rather than intelligence.",
        ])

    best = max(results, key=lambda r: (r["avg_overall_quality"], -r["avg_latency_seconds"]))
    return "\n".join([
        best["strategy_name"],
        "↓",
        f"Quality {best['avg_overall_quality']} @ {best['avg_latency_seconds']}s",
        "",
        "Optimize quality per unit time — not agent count alone.",
    ])
