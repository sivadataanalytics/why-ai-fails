"""
Series 2.5 — Long-Term AI Memory Engineering Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
Long-term memory is NOT a conversation archive — it is a compressed knowledge base.

500 conversations → extract memories → compress → retrieve top-K → inject into prompt

ARCHITECTURE
------------
  500 Conversations
        ↓
  Memory Extractor
        ↓
  Memory Compressor (dedup / consolidate / update / expire)
        ↓
  Memory Store (structured JSON profile)
        ↓
  Memory Retriever (top-K for user request)
        ↓
  Prompt Builder → Gemini

READING ORDER
-------------
1. conversations.py       — 500 simulated conversations
2. memory_extractor.py    — structured memory extraction
3. memory_compressor.py   — dedup, consolidate, update, expire
4. memory_store.py        — JSON profile storage
5. memory_retriever.py    — intent + keyword ranking
6. evaluator.py           — retrieval accuracy metrics
7. app.py main()          — benchmark flow
8. benchmark.py           — comparison printer

RUN
---
  python series-2.5/app.py --dry-run
  python series-2.5/app.py --strategy retrieval
  python series-2.5/app.py --question-id q1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).parent)]

from benchmark import print_benchmark
from common.config import load_config
from common.token_usage import estimate_cost, estimate_tokens
from conversation_loader import load_conversations
from conversations import CONVERSATION_COUNT, QUESTIONS_BY_ID
from evaluator import matched_memories, personalization_accuracy, retrieval_accuracy
from memory_compressor import compress
from memory_extractor import extract_all
from memory_retriever import retrieve_top_k
from memory_store import MemoryStore
from prompts import build_memory_prompt

DEFAULT_STRATEGIES = ["raw", "dedup", "compressed", "retrieval"]
DEFAULT_QUESTION_ID = "q1"
DEFAULT_TOP_K = 5

STRATEGIES: dict[str, dict[str, Any]] = {
    "raw": {
        "name": "NO COMPRESSION",
        "compression": "raw",
        "use_retrieval": False,
    },
    "dedup": {
        "name": "DEDUPLICATION",
        "compression": "dedup",
        "use_retrieval": False,
    },
    "compressed": {
        "name": "FULL COMPRESSION",
        "compression": "compressed",
        "use_retrieval": False,
    },
    "retrieval": {
        "name": "COMPRESSION + RETRIEVAL",
        "compression": "compressed",
        "use_retrieval": True,
    },
}

DRY_RUN_COMPLETION_TOKENS = 450
DRY_RUN_LATENCY_BASE_SEC = 0.8
DRY_RUN_LATENCY_PER_1K_PROMPT_SEC = 0.4


def estimate_latency(prompt_tokens: int, *, live_latency: float | None = None) -> float:
    if live_latency is not None:
        return live_latency
    return round(
        DRY_RUN_LATENCY_BASE_SEC + (prompt_tokens / 1000) * DRY_RUN_LATENCY_PER_1K_PROMPT_SEC,
        2,
    )


def run_strategy(
    strategy_key: str,
    raw_memories: list[dict[str, Any]],
    question: dict[str, Any],
    *,
    dry_run: bool,
    top_k: int,
) -> dict[str, Any]:
    """
    Run one memory strategy end-to-end.

    Flow:
      compress → store → (optional retrieve top-K) → build prompt → metrics
    """
    cfg = STRATEGIES[strategy_key]
    compressed = compress(raw_memories, level=cfg["compression"])
    store = MemoryStore(compressed)

    # Select memories injected into the prompt
    if cfg["use_retrieval"]:
        injected = retrieve_top_k(
            question["question"],
            store.memories,
            top_k=top_k,
            intent_keywords=question.get("intent_keywords"),
        )
    else:
        injected = store.memories

    memory_context = store.to_context_text(injected)
    prompt = build_memory_prompt(question["question"], memory_context)
    prompt_tokens = estimate_tokens(prompt)

    completion_tokens = DRY_RUN_COMPLETION_TOKENS
    latency_seconds = estimate_latency(prompt_tokens)
    text = "[dry-run: skipped Gemini call]"

    if not dry_run:
        from common.gemini_client import generate

        api = generate(prompt)
        prompt_tokens = api["prompt_tokens"]
        completion_tokens = api["completion_tokens"]
        latency_seconds = api["latency_seconds"]
        text = api["text"]

    ret_acc = retrieval_accuracy(injected, question.get("expected_memories"))
    pers_acc = personalization_accuracy(injected, question["expected_memories"])

    return {
        "strategy_key": strategy_key,
        "strategy_name": cfg["name"],
        "memory_size": store.size(),
        "memory_records": store.count(),
        "raw_records": len(raw_memories),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": latency_seconds,
        "estimated_cost": estimate_cost(prompt_tokens, completion_tokens),
        "retrieval_accuracy": ret_acc,
        "personalization_accuracy": pers_acc,
        "matched_memories": matched_memories(injected, question["expected_memories"]),
        "injected_count": len(injected),
        "text": text,
    }


def main(argv: list[str] | None = None) -> int:
    # STEP 0 — CLI
    parser = argparse.ArgumentParser(description="Long-term memory compression benchmark")
    parser.add_argument("--dry-run", action="store_true", help="No Gemini calls")
    parser.add_argument("--strategy", choices=list(STRATEGIES.keys()))
    parser.add_argument("--question-id", choices=list(QUESTIONS_BY_ID.keys()))
    parser.add_argument("--conversations", type=int, default=CONVERSATION_COUNT)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args(argv)

    load_config()

    # STEP 1 — Load 500 simulated conversations (same user)
    conversations = load_conversations(args.conversations)
    question = QUESTIONS_BY_ID[args.question_id or DEFAULT_QUESTION_ID]
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(conversations)} conversations for user {conversations[0]['user_id']}.")
    print(f"Benchmark question ({question['id']}): \"{question['question']}\"")
    print(f"Strategies: {', '.join(strategies)} | Top-K: {args.top_k}")
    print("Mode: dry-run (no API)\n" if args.dry_run else "Mode: live (Gemini per strategy)\n")

    # STEP 2 — Extract raw memories from all conversations
    print("Extracting memories from conversations ...")
    raw_memories = extract_all(conversations)
    print(f"Raw memories extracted: {len(raw_memories)}\n")

    # STEP 3–6 — Run each strategy and collect metrics
    results: list[dict[str, Any]] = []
    for strategy_key in strategies:
        if not args.dry_run:
            print(f"Calling Gemini ({STRATEGIES[strategy_key]['name']}) ...")
        try:
            result = run_strategy(
                strategy_key,
                raw_memories,
                question,
                dry_run=args.dry_run,
                top_k=args.top_k,
            )
        except ValueError as exc:
            print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
            return 1
        except Exception as exc:
            print(f"API error: {exc}\nTip: use --dry-run")
            return 1
        results.append(result)

    # STEP 7 — Print benchmark
    print_benchmark(results)

    if args.dry_run:
        print("\n--- Retrieval detail ---")
        for r in results:
            print(
                f"{r['strategy_name']}: records={r['memory_records']} "
                f"injected={r['injected_count']} matched={r['matched_memories']}"
            )

    if not args.dry_run:
        best = max(results, key=lambda r: (r["retrieval_accuracy"], -r["prompt_tokens"]))
        print("\n--- Answer excerpt (best accuracy / lowest tokens) ---")
        print(best["text"][:600])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
