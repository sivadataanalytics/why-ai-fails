"""
Series 2.2 — Prompt Caching demo (start reading here).

WHAT THIS DEMO PROVES
---------------------
Series 2.1 (Context Pruning)  → send LESS evidence (filter logs first).
Series 2.2 (Prompt Caching)   → don't RE-PROCESS the same stable text every time.

Think of the final prompt in two layers:

    ┌─────────────────────────────────────┐
    │  STATIC (cacheable)                 │  role, rules, schema, output format
    │  built by build_static_prompt()     │  same for every investigation
    ├─────────────────────────────────────┤
    │  DYNAMIC (never cache)              │  user question + pruned evidence
    │  built by build_dynamic_prompt()    │  changes every request
    └─────────────────────────────────────┘

READING ORDER
-------------
1. prompt_cache.py  — what gets cached, billable_tokens(), PromptCache.resolve()
2. app.py main()    — step-by-step flow (numbered below)
3. benchmark.py     — how savings are printed

RUN
---
  python app.py --dry-run      # token math only, $0, instant
  python app.py                # one Gemini call, live answer
  python app.py --drift-demo   # show v1/v2/v3 cache growth
  python app.py --cache-version v2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# BOOTSTRAP — Python needs these folders on sys.path to find our imports:
#   ROOT          → common/ (config, gemini_client, prompt_builder, ...)
#   series-1      → prune.py (context pruning, article 2.1)
#   this folder   → prompt_cache.py, benchmark.py (prompt caching, article 2.2)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "series-1"), str(Path(__file__).parent)]

from benchmark import print_benchmark
from common.config import DEFAULT_LOG_FILE, DEFAULT_QUESTION, load_config
from common.gemini_client import generate
from common.prompt_builder import build_dynamic_prompt, build_full_prompt
from common.token_usage import estimate_cost, estimate_input_cost, estimate_tokens
from common.utils import load_hdfs_logs
from prune import prune_hdfs_context
from prompt_cache import PromptCache, billable_tokens, build_static_prompt, print_drift_demo


def make_result(
    static: str,
    dynamic: str,
    *,
    cache_hit: bool,
    cache_entry: dict | None,
    api: dict | None,
    latency_scale: float = 1.0,
) -> dict:
    """
    Build one row of benchmark numbers (for "without cache" OR "with cache").

    Parameters
    ----------
    static, dynamic : the two prompt layers (see module docstring above)
    cache_hit       : False = pay for full static text every time
                      True  = static text read from cache (cheaper)
    cache_entry     : cache metadata (key, token count); None when no cache
    api             : Gemini response dict, or None in --dry-run mode
    latency_scale   : multiply API latency to model faster cache hits
                      (less input to process → lower latency)

    Example token math (typical v1 run):
      static ≈ 366 tokens, dynamic ≈ 144 tokens
      WITHOUT cache: 366 + 144 = 510 prompt tokens billed
      WITH cache:    144 + 12  = 156 prompt tokens billed (12 = cache ref)
    """
    # Step A — count tokens in each layer
    static_t = estimate_tokens(static)
    dynamic_t = estimate_tokens(dynamic)

    # Step B — apply cache accounting (see prompt_cache.billable_tokens)
    prompt_t, cached_t = billable_tokens(static_t, dynamic_t, cache_hit)

    # Step C — attach Gemini output when live; use zeros when --dry-run
    if api:
        completion = api["completion_tokens"]   # model output (same for both flows)
        latency = round(api["latency_seconds"] * latency_scale, 2)
        text = api["text"]
    else:
        completion = 0
        latency = 0.0
        text = "[dry-run: skipped Gemini call]"

    # Step D — package everything the benchmark printer expects
    return {
        "text": text,
        "prompt_tokens": prompt_t,              # input tokens we count for this flow
        "completion_tokens": completion,
        "total_tokens": prompt_t + completion,
        "input_cost": estimate_input_cost(prompt_t, cached_prompt_tokens=cached_t),
        "latency_seconds": latency,
        "estimated_cost": estimate_cost(prompt_t, completion, cached_prompt_tokens=cached_t),
        "cache_hit": cache_hit,
        "cache_key": cache_entry["cache_key"] if cache_entry else "",
        "cached_prompt_tokens": cached_t,       # static portion billed at discount
    }


def cost_for_n_requests(
    static_t: int, dynamic_t: int, completion: int, n: int, *, use_cache: bool
) -> float:
    """
    Answer: "What if we serve n identical requests?"

    Without cache → pay full static input on EVERY request (expensive at scale).
    With cache    → pay discounted static input every time (after warm-up).

    This is why prompt caching matters most in production chat / agent apps
    where the same system prompt is reused hundreds of times per hour.
    """
    # Pricing for one request in each mode
    miss_prompt, _ = billable_tokens(static_t, dynamic_t, cache_hit=False)
    hit_prompt, hit_cached = billable_tokens(static_t, dynamic_t, cache_hit=True)

    per_request = (
        estimate_cost(hit_prompt, completion, cached_prompt_tokens=hit_cached)
        if use_cache
        else estimate_cost(miss_prompt, completion, cached_prompt_tokens=0)
    )
    return round(per_request * n, 6)


def main(argv: list[str] | None = None) -> int:
    # -----------------------------------------------------------------------
    # STEP 0 — Parse command-line flags
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Prompt caching benchmark")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--cache-version", default="v1", choices=["v1", "v2", "v3"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--drift-demo", action="store_true")
    args = parser.parse_args(argv)

    load_config()  # reads GEMINI_API_KEY from .env when doing live runs

    # -----------------------------------------------------------------------
    # STEP 1 (optional) — Knowledge drift demo only; skip logs and API
    # -----------------------------------------------------------------------
    if args.drift_demo:
        print_drift_demo()
        return 0

    if not args.log_file.exists():
        print(f"Log file not found: {args.log_file}")
        return 1

    # -----------------------------------------------------------------------
    # STEP 2 — Load logs and prune (Series 2.1 still applies here)
    #          2000 lines → ~2 relevant lines + evidence summary
    # -----------------------------------------------------------------------
    logs = load_hdfs_logs(args.log_file)
    _, evidence = prune_hdfs_context(logs, args.question)

    # -----------------------------------------------------------------------
    # STEP 3 — Build the two prompt layers
    #          static  = from prompt_cache.py (CACHEABLE)
    #          dynamic = question + evidence   (NEVER CACHE)
    # -----------------------------------------------------------------------
    static = build_static_prompt(args.cache_version)
    dynamic = build_dynamic_prompt(args.question, evidence)

    print(f"Loaded {len(logs)} log lines.")
    print(f'Question: "{args.question}"')
    print(f"Static tokens: {estimate_tokens(static)} | Dynamic tokens: {estimate_tokens(dynamic)}\n")

    # -----------------------------------------------------------------------
    # STEP 4 — Call Gemini once (live mode only)
    #          Both benchmark rows share this answer — we only compare how
    #          input tokens would be billed differently, not the output text.
    # -----------------------------------------------------------------------
    api = None
    if not args.dry_run:
        print("Calling Gemini once ...")
        try:
            api = generate(build_full_prompt(static, dynamic))
        except ValueError as exc:
            print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
            return 1
        except Exception as exc:
            print(f"API error: {exc}\nTip: use --dry-run")
            return 1
        print("Done.\n")

    # -----------------------------------------------------------------------
    # STEP 5 — RUN 1: pretend caching does not exist
    #          Every request re-sends and re-processes the full static block.
    # -----------------------------------------------------------------------
    without = make_result(static, dynamic, cache_hit=False, cache_entry=None, api=api)

    # -----------------------------------------------------------------------
    # STEP 6 — RUN 2: simulate a warm cache
    #          1st resolve() → MISS (store static prompt in cache)
    #          2nd resolve() → HIT  (read static prompt from cache)
    #          In production, the 1st user pays "miss" cost; everyone after
    #          gets "hit" pricing on the static portion.
    # -----------------------------------------------------------------------
    cache = PromptCache()
    cache.resolve(args.cache_version, static)              # miss
    entry, hit = cache.resolve(args.cache_version, static)  # hit

    # Scale latency down on cache hit (fewer input tokens to process)
    latency_scale = 1.0
    if api and without["prompt_tokens"] > 0:
        cached_prompt, _ = billable_tokens(
            estimate_tokens(static), estimate_tokens(dynamic), cache_hit=True
        )
        latency_scale = cached_prompt / without["prompt_tokens"]

    with_cache = make_result(
        static, dynamic, cache_hit=hit, cache_entry=entry, api=api, latency_scale=latency_scale
    )

    # -----------------------------------------------------------------------
    # STEP 7 — Project cost for 100 requests (shows compounding savings)
    # -----------------------------------------------------------------------
    static_t = estimate_tokens(static)
    dynamic_t = estimate_tokens(dynamic)
    completion = api["completion_tokens"] if api else 0
    cost_100_without = cost_for_n_requests(static_t, dynamic_t, completion, 100, use_cache=False)
    cost_100_with = cost_for_n_requests(static_t, dynamic_t, completion, 100, use_cache=True)

    # -----------------------------------------------------------------------
    # STEP 8 — Print side-by-side benchmark
    # -----------------------------------------------------------------------
    print_benchmark(
        without,
        with_cache,
        hit_ratio_pct=cache.hit_ratio_pct(),
        cost_100_without=cost_100_without,
        cost_100_with=cost_100_with,
    )

    if api:
        print("\n--- Answer (excerpt) ---")
        print(with_cache["text"][:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
