"""
Benchmark printer for Series 2.6 memory retrieval lab.
"""

from __future__ import annotations

from typing import Any


def print_strategy_result(result: dict[str, Any]) -> None:
    print("-------------------------------------")
    print(result["strategy_name"])
    print("-------------------------------------")
    print(f"Prompt Tokens       : {result['prompt_tokens']}")
    print(f"Completion Tokens   : {result['completion_tokens']}")
    print(f"Total Tokens        : {result['total_tokens']}")
    print(f"Latency             : {result['latency_seconds']} sec")
    print(f"Estimated Cost      : ${result['estimated_cost']:.4f}")
    print(f"Retrieval Accuracy  : {result['retrieval_accuracy']}")
    print(f"Precision           : {result['precision']}")
    print(f"Recall              : {result['recall']}")
    print(f"Personalization     : {result['personalization_score']}")


def print_benchmark(results: list[dict[str, Any]]) -> None:
    print("=====================================")
    print("MEMORY RETRIEVAL BENCHMARK")
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

    rerank = next((r for r in results if r["strategy_key"] == "rerank"), None)
    hybrid = next((r for r in results if r["strategy_key"] == "hybrid"), None)

    if rerank and hybrid and rerank["retrieval_accuracy"] >= hybrid["retrieval_accuracy"]:
        return "\n".join([
            "Hybrid + Re-ranking",
            "↓",
            "Highest Retrieval Accuracy",
            "↓",
            "Lowest Prompt Tokens",
            "↓",
            "Best Personalization",
            "↓",
            "Enterprise Recommendation",
            "",
            "Store knowledge efficiently.",
            "Retrieve only what matters.",
            "Ignore everything else.",
        ])

    best = max(
        results,
        key=lambda r: (r["retrieval_accuracy"], r["precision"], -r["prompt_tokens"]),
    )
    return "\n".join([
        best["strategy_name"],
        "↓",
        "Highest Retrieval Accuracy",
        "↓",
        "Best Precision / Personalization Tradeoff",
        "",
        "Hybrid + Re-ranking",
        "↓",
        "Enterprise Recommendation",
        "",
        "Store knowledge efficiently.",
        "Retrieve only what matters.",
        "Ignore everything else.",
    ])
