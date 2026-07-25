"""
Series 2.6 — Memory Retrieval Engineering Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
Building memory is only half the problem. Retrieving the right memory is what
makes AI intelligent.

100,000 memory records → retrieval strategy → top-K → prompt → Gemini

ARCHITECTURE
------------
  User Request
        ↓
  Intent Detection
        ↓
  Memory Search (keyword / semantic / hybrid)
        ↓
  Memory Ranking (+ re-ranking)
        ↓
  Top-K Selection
        ↓
  Prompt Builder → Gemini

READING ORDER
-------------
1. memories.py      — 100k synthetic memory dataset
2. memory_store.py  — inverted index + TF-IDF
3. retriever.py     — four retrieval strategies
4. ranking.py       — re-ranking formula
5. evaluator.py     — precision, recall, accuracy
6. app.py main()    — benchmark flow
7. benchmark.py     — comparison printer

RUN
---
  python series-2.6/app.py --dry-run
  python series-2.6/app.py --strategy rerank
  python series-2.6/app.py --query-id q2 --top-k 5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).parent)]

from benchmark import print_benchmark
from common.config import load_config
from common.token_usage import estimate_cost, estimate_tokens
from evaluator import (
    matched_values,
    personalization_score,
    precision,
    recall,
    retrieval_accuracy,
)
from memory_store import MemoryStore
from memories import MEMORY_COUNT
from prompts import build_retrieval_prompt
from queries import DEFAULT_QUERY_ID, QUERIES_BY_ID
from retriever import STRATEGIES, STRATEGY_NAMES, retrieve

DEFAULT_STRATEGIES = list(STRATEGIES)
DRY_RUN_COMPLETION_TOKENS = 400
DRY_RUN_LATENCY_BASE_SEC = 0.5
DRY_RUN_LATENCY_PER_1K_PROMPT_SEC = 0.35
DRY_RUN_LATENCY_RETRIEVAL_SEC = 0.5


def estimate_latency(
    prompt_tokens: int,
    *,
    retrieval_seconds: float,
    live_latency: float | None = None,
) -> float:
    if live_latency is not None:
        return live_latency
    return round(
        DRY_RUN_LATENCY_BASE_SEC
        + retrieval_seconds
        + (prompt_tokens / 1000) * DRY_RUN_LATENCY_PER_1K_PROMPT_SEC,
        2,
    )


def run_strategy(
    strategy: str,
    store: MemoryStore,
    query: dict[str, Any],
    *,
    dry_run: bool,
    top_k: int,
) -> dict[str, Any]:
    """Run one retrieval strategy and collect benchmark metrics."""
    t0 = time.perf_counter()
    retrieved = retrieve(
        store,
        query["query"],
        strategy,
        top_k=top_k,
        intent_keywords=query.get("intent_keywords"),
    )
    retrieval_seconds = time.perf_counter() - t0

    prompt = build_retrieval_prompt(query["query"], retrieved)
    prompt_tokens = estimate_tokens(prompt)

    completion_tokens = DRY_RUN_COMPLETION_TOKENS
    latency_seconds = estimate_latency(prompt_tokens, retrieval_seconds=retrieval_seconds)
    text = "[dry-run: skipped Gemini call]"

    if not dry_run:
        from common.gemini_client import generate

        api = generate(prompt)
        prompt_tokens = api["prompt_tokens"]
        completion_tokens = api["completion_tokens"]
        latency_seconds = api["latency_seconds"]
        text = api["text"]

    expected = query["expected_values"]
    return {
        "strategy_key": strategy,
        "strategy_name": STRATEGY_NAMES[strategy],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": latency_seconds,
        "estimated_cost": estimate_cost(prompt_tokens, completion_tokens),
        "retrieval_accuracy": retrieval_accuracy(retrieved, expected),
        "precision": precision(retrieved, expected),
        "recall": recall(retrieved, store.memories, expected),
        "personalization_score": personalization_score(retrieved, expected),
        "matched_values": matched_values(retrieved, expected),
        "retrieved_count": len(retrieved),
        "retrieval_seconds": round(retrieval_seconds, 3),
        "text": text,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memory retrieval benchmark")
    parser.add_argument("--dry-run", action="store_true", help="No Gemini calls")
    parser.add_argument("--strategy", choices=list(STRATEGIES))
    parser.add_argument("--query-id", choices=list(QUERIES_BY_ID.keys()))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--memories", type=int, default=MEMORY_COUNT, help="Memory store size")
    args = parser.parse_args(argv)

    load_config()

    query = QUERIES_BY_ID[args.query_id or DEFAULT_QUERY_ID]
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loading {args.memories:,} memory records ...")
    t0 = time.perf_counter()
    store = MemoryStore.load(args.memories)
    load_seconds = time.perf_counter() - t0
    print(f"Indexed {store.size():,} memories in {load_seconds:.1f}s")
    print(f"Query ({query['id']}): \"{query['query']}\"")
    print(f"Strategies: {', '.join(strategies)} | Top-K: {args.top_k}")
    print("Mode: dry-run (no API)\n" if args.dry_run else "Mode: live (Gemini per strategy)\n")

    results: list[dict[str, Any]] = []
    for strategy in strategies:
        if not args.dry_run:
            print(f"Calling Gemini ({STRATEGY_NAMES[strategy]}) ...")
        try:
            result = run_strategy(
                strategy, store, query, dry_run=args.dry_run, top_k=args.top_k
            )
        except ValueError as exc:
            print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
            return 1
        except Exception as exc:
            print(f"API error: {exc}\nTip: use --dry-run")
            return 1
        results.append(result)

    print_benchmark(results)

    if args.dry_run:
        print("\n--- Retrieval detail ---")
        for r in results:
            print(
                f"{r['strategy_name']}: retrieved={r['retrieved_count']} "
                f"in {r['retrieval_seconds']}s matched={r['matched_values']}"
            )

    if not args.dry_run:
        best = max(results, key=lambda r: (r["retrieval_accuracy"], -r["prompt_tokens"]))
        print("\n--- Answer excerpt ---")
        print(best["text"][:600])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
