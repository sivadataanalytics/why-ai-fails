"""
Benchmark printer for Series 2.3 RAG chunking lab.

Compares chunking strategies side-by-side for one question and prints
an engineering observation based on hit scores and prompt tokens.
"""

from __future__ import annotations

from typing import Any


def print_strategy_result(strategy_result: dict[str, Any]) -> None:
    """Print one strategy's metrics block."""
    print("------------------------------------")
    print(strategy_result["strategy_name"])
    print("------------------------------------")
    print(f"Chunk Size       : {strategy_result.get('chunk_size', 'n/a')}")
    print(f"Overlap          : {strategy_result.get('overlap', 'n/a')}")
    print(f"Chunks Created   : {strategy_result['chunks_created']}")
    print(f"Top-K Retrieved  : {strategy_result['top_k_retrieved']}")
    print(f"Prompt Tokens    : {strategy_result['prompt_tokens']}")
    print(f"Completion Tokens: {strategy_result['completion_tokens']}")
    print(f"Total Tokens     : {strategy_result['total_tokens']}")
    print(f"Latency          : {strategy_result['latency_seconds']} sec")
    print(f"Estimated Cost   : ${strategy_result['estimated_cost']:.6f}")
    print(f"Hit Score        : {strategy_result['hit_score']}")


def print_benchmark(question: str, results: list[dict[str, Any]]) -> None:
    """Print full comparison for all strategies on one question."""
    print("====================================")
    print("RAG CHUNKING BENCHMARK")
    print("====================================")
    print()
    print("QUESTION:")
    print(question)
    print()

    for result in results:
        print_strategy_result(result)

    print()
    print("====================================")
    print("ENGINEERING OBSERVATION")
    print("====================================")
    print(_observation(results))
    print("====================================")


def _observation(results: list[dict[str, Any]]) -> str:
    """
    Pick a human-readable takeaway from the strategy comparison.

    Uses hit score first (quality), then prompt tokens (cost efficiency).
    """
    if not results:
        return "No results to compare."

    by_hit = sorted(results, key=lambda r: r["hit_score"], reverse=True)
    by_cost = sorted(results, key=lambda r: r["prompt_tokens"])

    best_hit = by_hit[0]
    cheapest = by_cost[0]

    lines: list[str] = []

    if best_hit["hit_score"] < 1.0:
        lines.append(
            f"{best_hit['strategy_name']} achieved the best hit score "
            f"({best_hit['hit_score']}) but may still miss some expected terms."
        )
    else:
        perfect = [r for r in results if r["hit_score"] >= 1.0]
        if len(perfect) > 1:
            names = ", ".join(r["strategy_name"] for r in perfect)
            lines.append(f"{names} all retrieved the required terms (hit score 1.00).")
        else:
            lines.append(
                f"{best_hit['strategy_name']} achieved a perfect hit score "
                f"({best_hit['hit_score']})."
            )

    if cheapest["strategy_name"] != best_hit["strategy_name"]:
        lines.append(
            f"{cheapest['strategy_name']} used the fewest prompt tokens "
            f"({cheapest['prompt_tokens']}) but hit score was {cheapest['hit_score']}."
        )

    # Cost vs quality tradeoff narrative
    small = next((r for r in results if "SMALL" in r["strategy_name"]), None)
    large = next((r for r in results if "LARGE" in r["strategy_name"]), None)
    medium = next((r for r in results if "MEDIUM" in r["strategy_name"]), None)

    if small and large:
        if small["hit_score"] < large["hit_score"]:
            lines.append(
                "Small chunks reduced cost but missed some context."
            )
        elif small["hit_score"] == large["hit_score"]:
            lines.append(
                "Small chunks matched large chunks on hit score at lower prompt cost."
            )
        if large["prompt_tokens"] > small["prompt_tokens"]:
            lines.append(
                "Large chunks preserved more text per retrieval but increased "
                "prompt size and latency."
            )

    if medium:
        others = [r for r in results if r is not medium]
        if medium["hit_score"] >= max((r["hit_score"] for r in others), default=0):
            if medium["prompt_tokens"] <= max(
                (r["prompt_tokens"] for r in others), default=0
            ):
                lines.append(
                    "Medium chunks provided a strong balance of retrieval quality "
                    "and prompt cost for this workload."
                )

    if not lines:
        lines.append(
            "Different chunk sizes produce different retrieval and cost profiles. "
            "Benchmark on your own corpus — do not guess."
        )

    return "\n".join(lines)
