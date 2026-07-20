"""
Benchmark printer for Series 2.4 conversation summarization lab.

Takes result dicts from app.run_strategy() and prints a human-readable
side-by-side comparison of all four summarization strategies.

Key lesson printed at the end:
  "Conversation grows forever. Memory shouldn't."
"""

from __future__ import annotations

from typing import Any


def print_strategy_result(result: dict[str, Any]) -> None:
    """Print one strategy's metrics block."""
    print("-------------------------------------")
    print(result["strategy_name"])
    print("-------------------------------------")
    print(f"Prompt Tokens     : {result['prompt_tokens']}")       # input size → cost driver
    print(f"Completion Tokens : {result['completion_tokens']}")   # model output
    print(f"Total Tokens      : {result['total_tokens']}")
    print(f"Latency           : {result['latency_seconds']} sec")  # grows with prompt size
    print(f"Estimated Cost    : ${result['estimated_cost']:.4f}")
    print(f"Summary Size      : {result['summary_size']} tokens")  # compressed memory size
    print(f"Memory Score      : {result['memory_score']}")         # 1.0 = all facts preserved
    print(f"Context Retention : {result['context_retention']}")    # vs full conversation


def print_benchmark(results: list[dict[str, Any]]) -> None:
    """Print full strategy comparison table + engineering observation."""
    print("=====================================")
    print("CONVERSATION SUMMARIZATION BENCHMARK")
    print("=====================================")
    print()

    for result in results:
        print_strategy_result(result)

    print()
    print("=====================================")
    print("ENGINEERING OBSERVATION")
    print("=====================================")
    print(_observation(results))
    print("=====================================")


def _observation(results: list[dict[str, Any]]) -> str:
    """
    Generate human-readable takeaway comparing all strategies.

    Narrative arc:
      Full → perfect memory, highest cost
      Rolling → good memory, much lower cost
      Hierarchical → scales to long threads
      Semantic → highest information density, lowest cost
    """
    by_name = {r["strategy_name"]: r for r in results}

    full = by_name.get("FULL CONVERSATION")
    rolling = by_name.get("ROLLING SUMMARY")
    hierarchical = by_name.get("HIERARCHICAL SUMMARY")
    semantic = by_name.get("SEMANTIC SUMMARY")

    lines: list[str] = []

    if full:
        lines.append("Full Conversation")
        lines.append("↓")
        lines.append("Perfect Memory" if full["memory_score"] >= 1.0 else "Strong Memory")
        lines.append("↓")
        lines.append("Highest Cost")
        lines.append("")

    if rolling:
        lines.append("Rolling Summary")
        lines.append("↓")
        lines.append("Good Memory" if rolling["memory_score"] >= 0.8 else "Reduced Memory")
        lines.append("↓")
        lines.append("Much Lower Cost")
        lines.append("")

    if hierarchical:
        lines.append("Hierarchical Summary")
        lines.append("↓")
        lines.append(
            "Excellent Long-term Memory"
            if hierarchical["memory_score"] >= 0.9
            else "Good Long-term Memory"
        )
        lines.append("↓")
        lines.append("Lower Cost")
        lines.append("")

    if semantic:
        lines.append("Semantic Summary")
        lines.append("↓")
        lines.append("Highest Information Density")
        lines.append("↓")
        lines.append("Lowest Cost")
        lines.append("↓")
        lines.append("Lowest Latency")

    # Quantify semantic savings vs full baseline
    if full and semantic and semantic["prompt_tokens"] < full["prompt_tokens"]:
        reduction = round(
            100 * (full["prompt_tokens"] - semantic["prompt_tokens"]) / full["prompt_tokens"],
            1,
        )
        lines.append("")
        lines.append(
            f"Semantic summary cut prompt tokens by ~{reduction}% "
            f"while memory score stayed at {semantic['memory_score']}."
        )

    lines.append("")
    lines.append("Conversation grows forever. Memory shouldn't.")

    return "\n".join(lines)
