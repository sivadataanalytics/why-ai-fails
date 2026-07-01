"""
Token measurement and savings reporting.

Compares the two flows and prints how many tokens pruning saved.
Prompt token reduction is the primary metric — that's what you pay for.
"""

from __future__ import annotations

from typing import Any

from common.token_usage import pct_reduction


def print_benchmark(
    without: dict[str, Any],
    with_pruning: dict[str, Any],
    *,
    label_without: str = "WITHOUT PRUNING",
    label_with: str = "WITH PRUNING",
) -> dict[str, float]:
    """
    Side-by-side comparison of token usage and latency.

    Key metrics:
      prompt_reduction_pct  — input tokens saved (main cost driver)
      token_reduction_pct   — total tokens saved (input + output)
      latency_reduction_pct — wall-clock time saved (scales with prompt size)
    """
    savings = {
        "prompt_reduction_pct": pct_reduction(
            without["prompt_tokens"], with_pruning["prompt_tokens"]
        ),
        "latency_reduction_pct": pct_reduction(
            without["latency_seconds"], with_pruning["latency_seconds"]
        ),
        "token_reduction_pct": pct_reduction(
            without["total_tokens"], with_pruning["total_tokens"]
        ),
    }

    print("====================================")
    print("CONTEXT PRUNING BENCHMARK")
    print("====================================\n")

    _print_run(label_without, without)
    print()
    _print_run(label_with, with_pruning)
    print()
    print("SAVINGS")
    print(f"Prompt Reduction  : {savings['prompt_reduction_pct']}%")
    print(f"Latency Reduction : {savings['latency_reduction_pct']}%")
    print(f"Token Reduction   : {savings['token_reduction_pct']}%")
    print("====================================")

    return savings


def _print_run(label: str, result: dict[str, Any]) -> None:
    print(label)
    print(f"Prompt Tokens     : {result['prompt_tokens']}")
    print(f"Completion Tokens : {result['completion_tokens']}")
    print(f"Total Tokens      : {result['total_tokens']}")
    print(f"Latency           : {result['latency_seconds']} sec")
