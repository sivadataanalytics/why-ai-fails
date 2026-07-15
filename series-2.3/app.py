"""
Series 2.3 — RAG Chunking Benchmark Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
The same documents, same questions, and same model — only chunking strategy changes.

Chunk size directly affects:
  - Retrieval quality (Hit Score)
  - Prompt tokens
  - Latency
  - Estimated cost

READING ORDER
-------------
1. chunker.py    — fixed-size and semantic chunking
2. retriever.py  — keyword scoring and hit score
3. questions.py  — benchmark questions + expected terms
4. app.py main() — numbered flow below
5. benchmark.py  — comparison printer

RUN
---
  python series-2.3/app.py --dry-run
  python series-2.3/app.py
  python series-2.3/app.py --question-id q1
  python series-2.3/app.py --strategy medium
  python series-2.3/app.py --top-k 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# BOOTSTRAP — add repo root and this folder to sys.path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).parent)]

from benchmark import print_benchmark
from chunker import STRATEGIES, chunk_corpus
from common.config import load_config
from common.token_usage import estimate_cost, estimate_tokens
from prompt_builder import build_rag_prompt
from questions import QUESTIONS, QUESTIONS_BY_ID
from retriever import hit_score, matched_terms, retrieve_top_k

DOCS_DIR = ROOT / "docs"
DEFAULT_TOP_K = 3

# Dry-run estimates when Gemini is not called
DRY_RUN_COMPLETION_TOKENS = 300
DRY_RUN_LATENCY_BASE_SEC = 1.2
DRY_RUN_LATENCY_PER_1K_PROMPT_SEC = 0.6


def load_documents(docs_dir: Path) -> dict[str, str]:
    """Load all .txt files from docs/ into {stem: text}."""
    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    documents: dict[str, str] = {}
    for path in sorted(docs_dir.glob("*.txt")):
        documents[path.stem] = path.read_text(encoding="utf-8")
    if not documents:
        raise FileNotFoundError(f"No .txt documents found in {docs_dir}")
    return documents


def estimate_latency(prompt_tokens: int, *, live_latency: float | None = None) -> float:
    """Use API latency when available; otherwise model from prompt size."""
    if live_latency is not None:
        return live_latency
    return round(
        DRY_RUN_LATENCY_BASE_SEC + (prompt_tokens / 1000) * DRY_RUN_LATENCY_PER_1K_PROMPT_SEC,
        2,
    )


def run_strategy(
    strategy_key: str,
    question: dict[str, Any],
    documents: dict[str, str],
    *,
    top_k: int,
    dry_run: bool,
) -> dict[str, Any]:
    """
    Run one chunking strategy for one question.

    Flow: chunk corpus → retrieve top-k → build prompt → (optional) Gemini → metrics
    """
    strategy = STRATEGIES[strategy_key]
    chunks = chunk_corpus(documents, strategy_key)
    retrieved = retrieve_top_k(question["question"], chunks, top_k=top_k)
    prompt = build_rag_prompt(question["question"], retrieved)
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

    score = hit_score(retrieved, question["expected_terms"])

    return {
        "strategy_key": strategy_key,
        "strategy_name": strategy["name"],
        "chunk_size": strategy.get("chunk_size", "semantic"),
        "overlap": strategy.get("overlap", 0),
        "chunks_created": len(chunks),
        "top_k_retrieved": len(retrieved),
        "retrieved_chunks": retrieved,
        "matched_terms": matched_terms(retrieved, question["expected_terms"]),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": latency_seconds,
        "estimated_cost": estimate_cost(prompt_tokens, completion_tokens),
        "hit_score": score,
        "text": text,
    }


def main(argv: list[str] | None = None) -> int:
    # -----------------------------------------------------------------------
    # STEP 0 — Parse CLI flags
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="RAG chunking benchmark lab")
    parser.add_argument("--dry-run", action="store_true", help="No Gemini call; token estimates only")
    parser.add_argument("--question-id", choices=list(QUESTIONS_BY_ID.keys()))
    parser.add_argument("--strategy", choices=list(STRATEGIES.keys()))
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--docs-dir", type=Path, default=DOCS_DIR)
    args = parser.parse_args(argv)

    load_config()

    # -----------------------------------------------------------------------
    # STEP 1 — Load corpus documents
    # -----------------------------------------------------------------------
    try:
        documents = load_documents(args.docs_dir)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    questions = (
        [QUESTIONS_BY_ID[args.question_id]]
        if args.question_id
        else QUESTIONS
    )
    strategies = [args.strategy] if args.strategy else ["small", "medium", "large"]

    print(f"Loaded {len(documents)} documents from {args.docs_dir}")
    print(f"Strategies: {', '.join(strategies)} | Top-K: {args.top_k}")
    if args.dry_run:
        print("Mode: dry-run (no Gemini API calls)\n")
    else:
        print("Mode: live (Gemini will be called per strategy per question)\n")

    # -----------------------------------------------------------------------
    # STEP 2–7 — For each question, run each strategy and print benchmark
    # -----------------------------------------------------------------------
    for question in questions:
        results: list[dict[str, Any]] = []
        for strategy_key in strategies:
            if not args.dry_run:
                print(f"Calling Gemini ({STRATEGIES[strategy_key]['name']}) ...")
            try:
                result = run_strategy(
                    strategy_key,
                    question,
                    documents,
                    top_k=args.top_k,
                    dry_run=args.dry_run,
                )
            except ValueError as exc:
                print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
                return 1
            except Exception as exc:
                print(f"API error: {exc}\nTip: use --dry-run")
                return 1
            results.append(result)

        print_benchmark(question["question"], results)

        # Optional detail: which expected terms matched
        if args.dry_run or args.question_id:
            print("\n--- Retrieval detail ---")
            for r in results:
                print(f"{r['strategy_name']}: matched {r['matched_terms']}")

        if not args.dry_run:
            best = max(results, key=lambda r: (r["hit_score"], -r["prompt_tokens"]))
            print("\n--- Answer excerpt (best hit score) ---")
            print(best["text"][:600])
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
