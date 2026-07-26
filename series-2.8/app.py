"""
Series 2.8 — Multi-Agent Orchestration Engineering Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
Enterprise AI systems scale through coordination rather than intelligence.

500 enterprise requests → planner → scheduler → specialized agents
→ shared memory → aggregator → (reviewer) → benchmark

Four strategies compared:
  single      — one general agent (baseline)
  sequential  — specialized agents in dependency order
  parallel    — parallel waves where dependencies allow
  reviewer    — parallel + reviewer with one rework iteration

ARCHITECTURE
------------
  User Request → Planner → Task Decomposition → Scheduler
  → Specialized Agents → Shared Memory → Aggregator → Reviewer → Response

READING ORDER
-------------
1. tasks.py         — 500 enterprise requests
2. agents.py        — specialized agent pool
3. planner.py       — task decomposition
4. scheduler.py     — sequential / parallel scheduling
5. shared_memory.py — agent communication bus
6. orchestrator.py  — four strategies
7. reviewer.py      — quality validation + rework
8. app.py main()    — benchmark CLI

RUN
---
  python series-2.8/app.py --dry-run
  python series-2.8/app.py --strategy reviewer --dry-run
  python series-2.8/app.py --request-id r0024 --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).parent)]

from benchmark import print_benchmark, run_strategy
from common.config import load_config
from orchestrator import STRATEGIES, STRATEGY_NAMES, orchestrate
from prompts import build_orchestration_prompt, build_single_agent_prompt
from tasks import DEFAULT_REQUEST_ID, REQUESTS, REQUESTS_BY_ID, generate_requests

DEFAULT_STRATEGIES = list(STRATEGIES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-agent orchestration benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Simulate orchestration; no Gemini")
    parser.add_argument("--strategy", choices=list(STRATEGIES))
    parser.add_argument("--request-id", choices=list(REQUESTS_BY_ID.keys()))
    parser.add_argument("--requests", type=int, default=len(REQUESTS), help="Dataset size")
    args = parser.parse_args(argv)

    load_config()

    requests = generate_requests(args.requests) if args.requests != len(REQUESTS) else REQUESTS
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(requests):,} enterprise requests")
    print(f"Strategies: {', '.join(strategies)}")
    print("Mode: dry-run (simulated orchestration)\n" if args.dry_run else "Mode: live (Gemini for selected request)\n")

    if args.request_id:
        req = REQUESTS_BY_ID.get(args.request_id) or requests[0]
        for strategy in strategies:
            run = orchestrate(req, strategy, dry_run=args.dry_run)
            print(f"--- {STRATEGY_NAMES[strategy]} / {req['request_id']} ---")
            print(f"Prompt      : {req['prompt'][:70]}…")
            print(f"Agents run  : {len(run['agent_results'])}")
            print(f"Latency     : {run['latency_seconds']} sec")
            print(f"Quality     : {run['overall_quality']}")
            print(f"Completion  : {run['task_completion']}")
            print(f"Consistency : {run['consistency_score']}")
            print(f"Security    : {run['security_score']}")
            if run.get("review_score") is not None:
                print(f"Review      : {run['review_score']}")
            print(f"Tokens      : {run['total_tokens']} (prompt {run['prompt_tokens']})")
            print(f"Cost        : ${run['estimated_cost']:.4f}")
            print()

        if not args.dry_run:
            strategy = strategies[0]
            run = orchestrate(req, strategy, dry_run=False)
            from common.gemini_client import generate

            if strategy == "single":
                prompt = build_single_agent_prompt(req)
            else:
                prompt = build_orchestration_prompt(req, run)
            print(f"Calling Gemini ({STRATEGY_NAMES[strategy]}) ...")
            try:
                api = generate(prompt)
                print("\n--- Answer excerpt ---")
                print(api["text"][:600])
            except Exception as exc:
                print(f"API error: {exc}\nTip: use --dry-run")
                return 1
        return 0

    results: list[dict[str, Any]] = []
    for strategy in strategies:
        print(f"Running {STRATEGY_NAMES[strategy]} ...")
        results.append(run_strategy(strategy, requests, dry_run=True))

    print()
    print_benchmark(results)

    if args.dry_run and len(strategies) > 1:
        print("\n--- Quality detail ---")
        for r in results:
            print(
                f"{r['strategy_name']}: quality={r['avg_overall_quality']} "
                f"latency={r['avg_latency_seconds']}s "
                f"completion={r['avg_task_completion']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
