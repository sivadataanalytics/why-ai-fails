"""
Benchmark printer for Series 2.2.

Takes two result dicts from app.make_result() and prints a human-readable report.

Key idea: compare "without cache" vs "with cache" on the SAME Gemini answer.
We are measuring billing differences, not answer quality differences.
"""

from __future__ import annotations

from common.token_usage import pct_reduction


def print_benchmark(
    without: dict,
    with_cache: dict,
    *,
    hit_ratio_pct: float = 0.0,
    cost_100_without: float = 0.0,
    cost_100_with: float = 0.0,
) -> None:
    """Print the full side-by-side report."""
    # --- Section 1: expensive path (no caching) ---
    print("====================================")
    print("WITHOUT PROMPT CACHING")
    print("====================================")
    _rows(without)

    # --- Section 2: efficient path (cache hit) ---
    print("\n------------------------------------")
    print("WITH PROMPT CACHING")
    print("====================================")
    _rows(with_cache)

    # Extra cache metadata (only present on the "with" side)
    if with_cache.get("cache_hit") is not None:
        print(f"Cache Lookup      : {'HIT' if with_cache['cache_hit'] else 'MISS'}")
    if with_cache.get("cache_key"):
        print(f"Cache Key         : {with_cache['cache_key']}")

    # --- Section 3: single-request savings ---
    # Input Cost Reduction is the most important line for prompt caching.
    # Total Cost Reduction is lower when completion tokens dominate the bill.
    print("\n------------------------------------")
    print("SAVINGS (single request)")
    print(f"Prompt Reduction      : {pct_reduction(without['prompt_tokens'], with_cache['prompt_tokens'])}%")
    print(f"Input Cost Reduction  : {pct_reduction(without['input_cost'], with_cache['input_cost'])}%")
    print(f"Latency Reduction     : {pct_reduction(without['latency_seconds'], with_cache['latency_seconds'])}%")
    print(f"Total Cost Reduction  : {pct_reduction(without['estimated_cost'], with_cache['estimated_cost'])}%")
    print(f"Cache Hit Ratio       : {hit_ratio_pct}%")

    # --- Section 4: 100-request projection ---
    # Caching savings compound when the same static prompt serves many users.
    if cost_100_without > 0:
        print("\nSAVINGS (100 requests, cache warm)")
        print(f"Total Cost (no cache) : ${cost_100_without:.4f}")
        print(f"Total Cost (cached)   : ${cost_100_with:.4f}")
        print(f"Cost Reduction        : {pct_reduction(cost_100_without, cost_100_with)}%")
    print("====================================")


def _rows(r: dict) -> None:
    """Print one run's metrics. Each field comes from app.make_result()."""
    print(f"Prompt Tokens     : {r['prompt_tokens']}")       # input tokens counted for this flow
    print(f"Completion Tokens : {r['completion_tokens']}") # model output (usually identical both sides)
    print(f"Total Tokens      : {r['total_tokens']}")        # prompt + completion
    print(f"Input Cost        : ${r['input_cost']:.6f}")     # what caching reduces most
    print(f"Latency           : {r['latency_seconds']} sec")
    print(f"Estimated Cost    : ${r['estimated_cost']:.6f}")  # input + output cost
