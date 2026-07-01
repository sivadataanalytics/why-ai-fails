# Series 2.1 — Context Pruning demo
# Compares full HDFS log dump vs pruned block-scoped evidence sent to Gemini.
# Run: python demo.py [--dry-run] [--clarify-demo]

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

# Repo root on sys.path so `common.*` imports work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.benchmark import print_benchmark
from common.config import AMBIGUOUS_QUESTION, DEFAULT_LOG_FILE, DEFAULT_QUESTION, load_config
from common.gemini_client import generate
from common.prompt_builder import build_pruned_prompt, build_unpruned_prompt
from common.token_usage import estimate_tokens
from common.utils import is_ambiguous_question, load_hdfs_logs

# Load prune.py from same folder (folder name has dots, avoid package import)
_prune_path = Path(__file__).parent / "prune.py"
_spec = importlib.util.spec_from_file_location("prune_module", _prune_path)
_prune_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_prune_mod)
prune_hdfs_context = _prune_mod.prune_hdfs_context

# Clarify-first: ask scope before loading logs (zero tokens spent)
CLARIFYING_QUESTIONS = [
    "Which HDFS block ID should I investigate? (Example: blk_-8775602795571523802)",
    "What time window should I use?",
    "Are you looking for latency, errors, availability, or deployment failures?",
]


def print_clarification(question: str) -> None:
    print("====================================")
    print("CLARIFY FIRST — no logs retrieved yet")
    print("====================================")
    print(f'User: "{question}"\n')
    print("Assistant:")
    for i, q in enumerate(CLARIFYING_QUESTIONS, 1):
        print(f"  {i}. {q}")
    print("\n> Clarify first. Retrieve later.\n")


def run_without_pruning(question: str, raw_logs: str, *, dry_run: bool) -> dict:
    # Flow 1: naive app dumps entire log file into the prompt
    prompt = build_unpruned_prompt(question, raw_logs)
    if dry_run:
        pt = estimate_tokens(prompt)
        return {
            "text": "[dry-run: skipped Gemini call]",
            "prompt_tokens": pt,
            "completion_tokens": 0,
            "total_tokens": pt,
            "latency_seconds": 0.0,
        }
    return generate(prompt)


def run_with_pruning(question: str, logs_df, *, dry_run: bool) -> dict:
    # Flow 2: filter logs by block ID, summarize, send compact evidence only
    _, evidence = prune_hdfs_context(logs_df, question)
    prompt = build_pruned_prompt(question, evidence)
    if dry_run:
        pt = estimate_tokens(prompt)
        return {
            "text": "[dry-run: skipped Gemini call]",
            "prompt_tokens": pt,
            "completion_tokens": 0,
            "total_tokens": pt,
            "latency_seconds": 0.0,
            "evidence": evidence,
        }
    result = generate(prompt)
    result["evidence"] = evidence
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Context pruning benchmark (HDFS + Gemini)")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="Investigation question")
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE, help="HDFS log file")
    parser.add_argument("--dry-run", action="store_true", help="Token estimate only, no API call")
    parser.add_argument("--clarify-demo", action="store_true", help="Show clarify-first flow only")
    args = parser.parse_args(argv)

    load_config()

    if args.clarify_demo:
        print_clarification(AMBIGUOUS_QUESTION)
        return 0

    # Stop early if question has no block ID — don't waste tokens on vague requests
    if is_ambiguous_question(args.question):
        print_clarification(args.question)
        print("Re-run with a specific block ID, e.g.:")
        print(f'  python demo.py --question "{DEFAULT_QUESTION}"')
        return 0

    log_path = args.log_file
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return 1

    print(f"Loading HDFS logs from {log_path} ...")
    logs_df = load_hdfs_logs(log_path)
    raw_logs = "\n".join(logs_df["raw"].tolist())
    print(f"Loaded {len(logs_df)} log lines.\n")
    print(f'Question: "{args.question}"\n')

    print("Running WITHOUT context pruning ...")
    without = run_without_pruning(args.question, raw_logs, dry_run=args.dry_run)

    print("Running WITH context pruning ...")
    with_pruning = run_with_pruning(args.question, logs_df, dry_run=args.dry_run)

    print()
    print_benchmark(without, with_pruning)

    if not args.dry_run:
        print("\n--- WITH PRUNING — Gemini answer (excerpt) ---")
        print(with_pruning["text"][:800])
        if len(with_pruning["text"]) > 800:
            print("...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
