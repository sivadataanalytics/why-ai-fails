"""
Benchmark runner and printer for Series 2.7 model routing lab.
"""

from __future__ import annotations

from typing import Any

from evaluator import aggregate_metrics
from router import STRATEGY_NAMES, route_request


def run_strategy(
    strategy: str,
    requests: list[dict[str, Any]],
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Route all requests with one strategy and aggregate metrics."""
    results = [route_request(req, strategy, dry_run=dry_run) for req in requests]
    metrics = aggregate_metrics(results)
    return {
        "strategy_key": strategy,
        "strategy_name": STRATEGY_NAMES[strategy],
        "results": results,
        **metrics,
    }


def print_strategy_result(result: dict[str, Any]) -> None:
    print("-------------------------------------")
    print(result["strategy_name"])
    print("-------------------------------------")
    print(f"Average Cost        : ${result['avg_cost']:.4f}")
    print(f"Latency             : {result['avg_latency_seconds']} sec")
    print(f"Accuracy            : {result['accuracy']}")
    print(f"Prompt Tokens (avg) : {result['avg_prompt_tokens']}")
    print(f"Completion Tokens   : {result['avg_completion_tokens']}")
    print(f"Total Tokens (avg)  : {result['avg_total_tokens']}")
    if result["strategy_key"] == "confidence":
        print(f"Escalation Rate     : {result['escalation_rate'] * 100:.0f}%")


def print_model_utilization(result: dict[str, Any]) -> None:
    util = result.get("model_utilization", {})
    if not util:
        return
    print("Model Utilization   :")
    name_map = {
        "small": "Small Model",
        "medium_coding": "Coding Model",
        "medium_coding_internal": "Coding Model (Internal)",
        "large_reasoning": "Reasoning Model",
        "vision": "Vision Model",
        "large_general": "Large General LLM",
    }
    for mid, pct in util.items():
        label = name_map.get(mid, mid)
        print(f"  {label:<28} {pct}%")


def print_benchmark(results: list[dict[str, Any]]) -> None:
    print("=====================================")
    print("MODEL ROUTING BENCHMARK")
    print("=====================================")
    print()

    for result in results:
        print_strategy_result(result)
        print_model_utilization(result)
        print()

    print("=====================================")
    print("ENGINEERING RECOMMENDATION")
    print("=====================================")
    print(_recommendation(results))
    print("=====================================")


def _recommendation(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No results."

    smart = [r for r in results if r["strategy_key"] != "single"]
    confidence = next((r for r in smart if r["strategy_key"] == "confidence"), None)
    if confidence and confidence["accuracy"] >= 0.90:
        return "\n".join([
            "Confidence Routing",
            "↓",
            "Lowest Cost",
            "↓",
            "High Accuracy",
            "↓",
            f"Escalation Rate {confidence['escalation_rate'] * 100:.0f}%",
            "↓",
            "Enterprise Recommendation",
            "",
            "The best AI system is not the one with the biggest model.",
            "It is the one that knows when to use it.",
        ])

    best = min(smart or results, key=lambda r: (r["avg_cost"], -r["accuracy"]))
    return "\n".join([
        best["strategy_name"],
        "↓",
        "Best Cost / Accuracy Tradeoff",
        "",
        "Optimize the prompt.",
        "Optimize the memory.",
        "Optimize the model.",
    ])
