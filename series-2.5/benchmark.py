"""
Benchmark printer for Series 2.5 long-term memory lab.
"""

from __future__ import annotations

from typing import Any


def print_strategy_result(result: dict[str, Any]) -> None:
    """Print one strategy's metrics block."""
    print("-------------------------------------")
    print(result["strategy_name"])
    print("-------------------------------------")
    print(f"Memory Size       : {result['memory_size']}")
    print(f"Memory Records    : {result['memory_records']}")
    print(f"Prompt Tokens     : {result['prompt_tokens']}")
    print(f"Completion Tokens : {result['completion_tokens']}")
    print(f"Total Tokens      : {result['total_tokens']}")
    print(f"Latency           : {result['latency_seconds']} sec")
    print(f"Estimated Cost    : ${result['estimated_cost']:.4f}")
    print(f"Retrieval Accuracy: {result['retrieval_accuracy']}")
    print(f"Personalization   : {result['personalization_accuracy']}")


def print_benchmark(results: list[dict[str, Any]]) -> None:
    """Print full comparison table + engineering recommendation."""
    print("=====================================")
    print("LONG-TERM MEMORY BENCHMARK")
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
    lines: list[str] = []

    retrieval = next((r for r in results if "RETRIEVAL" in r["strategy_name"]), None)
    compressed = next((r for r in results if r["strategy_key"] == "compressed"), None)
    raw = next((r for r in results if r["strategy_key"] == "raw"), None)

    if retrieval:
        lines.append("Compression + Retrieval")
        lines.append("↓")
        lines.append("Lowest Prompt Tokens")
        lines.append("↓")
        lines.append("Lowest Latency")
        lines.append("↓")
        lines.append("Smallest Effective Memory In Prompt")
        if retrieval["retrieval_accuracy"] >= 1.0:
            lines.append("↓")
            lines.append("Perfect Retrieval Accuracy")

    if raw and retrieval and retrieval["prompt_tokens"] < raw["prompt_tokens"]:
        reduction = round(
            100 * (raw["prompt_tokens"] - retrieval["prompt_tokens"]) / raw["prompt_tokens"],
            1,
        )
        lines.append("")
        lines.append(
            f"Retrieval strategy cut prompt tokens by ~{reduction}% "
            f"vs no compression baseline."
        )

    if compressed:
        lines.append("")
        lines.append(
            f"Full compression reduced memory records from "
            f"{compressed.get('raw_records', '?')} → {compressed['memory_records']}."
        )

    lines.append("")
    lines.append("Long-term memory is not a conversation archive.")
    lines.append("Compress knowledge. Retrieve only what matters.")

    return "\n".join(lines)
