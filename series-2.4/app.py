"""
Series 2.4 — Conversation Summarization Engineering Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
Conversation summarization is memory management — not just token optimization.

Without summarization: 175 messages → huge prompt → high cost, high latency.
With summarization:    memory + latest messages → smaller prompt → preserved facts.

ARCHITECTURE
------------

  Without summarization:
    Conversation → 178 Messages → Prompt Builder → Gemini

  With summarization:
    Conversation → Summarizer → Conversation Memory + Latest Messages
                              → Prompt Builder → Gemini

  Gemini never receives the full conversation (except Strategy 1: full).

READING ORDER
-------------
1. conversation_dataset.py — synthetic 175-message enterprise conversation
2. summarizer.py          — full, rolling, hierarchical, semantic strategies
3. memory.py              — structured semantic memory extraction
4. evaluator.py           — Memory Score calculation
5. prompts.py             — prompt assembly (memory + latest vs full history)
6. app.py main()          — numbered STEPS 0–8 below
7. benchmark.py           — comparison printer

RUN
---
  python series-2.4/app.py --dry-run      # no API key, $0
  python series-2.4/app.py                # live Gemini (4 calls)
  python series-2.4/app.py --strategy rolling
  python series-2.4/app.py --question-id q3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# BOOTSTRAP — Python needs repo root + this folder on sys.path for imports
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).parent)]

from benchmark import print_benchmark
from common.config import load_config
from common.token_usage import estimate_cost, estimate_tokens
from conversation_dataset import BENCHMARK_QUESTIONS, QUESTIONS_BY_ID
from conversation_loader import load_conversation
from evaluator import context_retention, matched_facts, memory_score
from prompts import build_answer_prompt
from summarizer import STRATEGIES, apply_strategy

# All four strategies compared unless --strategy filters to one
DEFAULT_STRATEGIES = ["full", "rolling", "hierarchical", "semantic"]
DEFAULT_QUESTION_ID = "q5"  # "Summarize the current engineering objective."

# ---------------------------------------------------------------------------
# DRY-RUN PLACEHOLDERS — used when --dry-run skips Gemini
# Live mode replaces these with real values from usage_metadata
# ---------------------------------------------------------------------------
DRY_RUN_COMPLETION_TOKENS = 600
DRY_RUN_LATENCY_BASE_SEC = 1.0
DRY_RUN_LATENCY_PER_1K_PROMPT_SEC = 0.5


def estimate_latency(prompt_tokens: int, *, live_latency: float | None = None) -> float:
    """
    Estimate response latency from prompt size.

    Larger prompts → more input tokens for the model to process → higher latency.
    In live mode we use the actual wall-clock time from Gemini.
    """
    if live_latency is not None:
        return live_latency
    return round(
        DRY_RUN_LATENCY_BASE_SEC + (prompt_tokens / 1000) * DRY_RUN_LATENCY_PER_1K_PROMPT_SEC,
        2,
    )


def run_strategy(
    strategy_key: str,
    messages: list[dict[str, Any]],
    question: dict[str, Any],
    *,
    dry_run: bool,
    full_memory_score: float,
) -> dict[str, Any]:
    """
    Run one summarization strategy end-to-end and collect benchmark metrics.

    Flow per strategy:
      1. apply_strategy()  — compress history into memory + latest window
      2. build_answer_prompt() — assemble what Gemini would see
      3. generate()        — call Gemini (skipped in --dry-run)
      4. memory_score()    — did important facts survive summarization?

    Parameters
    ----------
    strategy_key      : full | rolling | hierarchical | semantic
    messages          : full 178-message conversation
    question          : benchmark question dict from conversation_dataset.py
    dry_run           : True → skip Gemini, use token estimates
    full_memory_score : baseline from full conversation (for context retention)
    """
    # STEP A — compress conversation using the chosen strategy
    packed = apply_strategy(messages, strategy_key)

    # STEP B — build the prompt Gemini receives (memory + latest OR full history)
    prompt = build_answer_prompt(
        question["question"],
        memory_text=packed["memory_text"],
        latest_messages=packed["latest_messages"],
        strategy_key=strategy_key,
    )
    prompt_tokens = estimate_tokens(prompt)

    # STEP C — default to dry-run placeholders; overwrite if live
    completion_tokens = DRY_RUN_COMPLETION_TOKENS
    latency_seconds = estimate_latency(prompt_tokens)
    text = "[dry-run: skipped Gemini call]"

    if not dry_run:
        # Lazy import — avoids loading google-genai when using --dry-run
        from common.gemini_client import generate

        api = generate(prompt)
        prompt_tokens = api["prompt_tokens"]       # real billed input tokens
        completion_tokens = api["completion_tokens"]
        latency_seconds = api["latency_seconds"]
        text = api["text"]

    # STEP D — evaluate memory quality (works in both dry-run and live)
    score = memory_score(packed["memory_text"], packed["latest_messages"])
    retention = context_retention(score, full_memory_score)

    # STEP E — package everything benchmark.py expects
    return {
        "strategy_key": strategy_key,
        "strategy_name": packed["strategy_name"],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": latency_seconds,
        "estimated_cost": estimate_cost(prompt_tokens, completion_tokens),
        "summary_size": packed["summary_size"],
        "memory_score": score,
        "context_retention": retention,
        "matched_facts": matched_facts(packed["memory_text"], packed["latest_messages"]),
        "message_count_in_prompt": packed["message_count_in_prompt"],
        "text": text,
    }


def main(argv: list[str] | None = None) -> int:
    # -----------------------------------------------------------------------
    # STEP 0 — Parse CLI flags
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Conversation summarization benchmark")
    parser.add_argument("--dry-run", action="store_true", help="No Gemini calls")
    parser.add_argument("--strategy", choices=list(STRATEGIES.keys()))
    parser.add_argument("--question-id", choices=list(QUESTIONS_BY_ID.keys()))
    args = parser.parse_args(argv)

    load_config()  # reads GEMINI_API_KEY from .env when doing live runs

    # -----------------------------------------------------------------------
    # STEP 1 — Load the synthetic enterprise conversation (~178 messages)
    # -----------------------------------------------------------------------
    messages = load_conversation()
    question = QUESTIONS_BY_ID[args.question_id or DEFAULT_QUESTION_ID]
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(messages)} conversation messages.")
    print(f"Benchmark question ({question['id']}): \"{question['question']}\"")
    print(f"Strategies: {', '.join(strategies)}")
    print("Mode: dry-run (no API)\n" if args.dry_run else "Mode: live (Gemini per strategy)\n")

    # -----------------------------------------------------------------------
    # STEP 2 — Establish baseline: full conversation memory score = 1.00 reference
    # Other strategies compare their retention against this baseline
    # -----------------------------------------------------------------------
    full_packed = apply_strategy(messages, "full")
    full_score = memory_score(full_packed["memory_text"], full_packed["latest_messages"])

    # -----------------------------------------------------------------------
    # STEP 3–6 — Run each strategy, collect metrics, optionally call Gemini
    # -----------------------------------------------------------------------
    results: list[dict[str, Any]] = []
    for strategy_key in strategies:
        if not args.dry_run:
            print(f"Calling Gemini ({STRATEGIES[strategy_key]['name']}) ...")
        try:
            result = run_strategy(
                strategy_key,
                messages,
                question,
                dry_run=args.dry_run,
                full_memory_score=full_score,
            )
        except ValueError as exc:
            print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
            return 1
        except Exception as exc:
            print(f"API error: {exc}\nTip: use --dry-run")
            return 1
        results.append(result)

    # -----------------------------------------------------------------------
    # STEP 7 — Print side-by-side benchmark + engineering observation
    # -----------------------------------------------------------------------
    print_benchmark(results)

    # Show which expected facts survived in each strategy (dry-run detail)
    if args.dry_run:
        print("\n--- Memory detail ---")
        for r in results:
            print(f"{r['strategy_name']}: matched {r['matched_facts']}")

    # -----------------------------------------------------------------------
    # STEP 8 — Live mode: show answer from best strategy (highest memory, lowest tokens)
    # -----------------------------------------------------------------------
    if not args.dry_run:
        best = max(results, key=lambda r: (r["memory_score"], -r["prompt_tokens"]))
        print("\n--- Answer excerpt (best memory / lowest tokens) ---")
        print(best["text"][:600])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
