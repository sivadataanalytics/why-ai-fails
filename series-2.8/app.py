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

Live mode calls Gemini for every agent. Dry-run uses computed local simulation.

RUN
---
  python series-2.8/app.py --dry-run
  python series-2.8/app.py --strategy reviewer --dry-run
  python series-2.8/app.py --request-id r0024 --live          # one request, all agents → Gemini
  python series-2.8/app.py --live --live-limit 3            # benchmark first 3 requests live
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
from tasks import DEFAULT_REQUEST_ID, REQUESTS, REQUESTS_BY_ID, generate_requests

DEFAULT_STRATEGIES = list(STRATEGIES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-agent orchestration benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Simulate orchestration; no Gemini")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call Gemini for each agent (requires GEMINI_API_KEY)",
    )
    parser.add_argument("--strategy", choices=list(STRATEGIES))
    parser.add_argument("--request-id", choices=list(REQUESTS_BY_ID.keys()))
    parser.add_argument("--requests", type=int, default=len(REQUESTS), help="Dataset size")
    parser.add_argument(
        "--live-limit",
        type=int,
        default=1,
        help="Max requests to run live when --live (default 1; use small values to control cost)",
    )
    args = parser.parse_args(argv)

    dry_run = not args.live
    if args.dry_run and args.live:
        print("Use either --dry-run or --live, not both.")
        return 1

    load_config()

    requests = generate_requests(args.requests) if args.requests != len(REQUESTS) else REQUESTS
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(requests):,} enterprise requests")
    print(f"Strategies: {', '.join(strategies)}")
    if dry_run:
        print("Mode: dry-run (simulated agents, computed metrics)\n")
    else:
        print(f"Mode: live (Gemini per agent, up to {args.live_limit} request(s) per strategy)\n")

    if args.request_id:
        req = REQUESTS_BY_ID.get(args.request_id) or requests[0]
        for strategy in strategies:
            run = orchestrate(req, strategy, dry_run=dry_run)
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
            if not dry_run and run["agent_results"]:
                print("\n--- Agent excerpt ---")
                print(run["agent_results"][-1]["output_text"][:400])
            print()
        return 0

    live_requests = requests[: args.live_limit] if not dry_run else requests

    if not dry_run and args.live_limit < len(requests):
        print(
            f"Live limit: running {len(live_requests)} of {len(requests)} requests "
            f"(increase --live-limit to run more; each request invokes multiple Gemini calls)\n"
        )

    results: list[dict[str, Any]] = []
    for strategy in strategies:
        print(f"Running {STRATEGY_NAMES[strategy]} ...")
        try:
            results.append(run_strategy(strategy, live_requests, dry_run=dry_run))
        except ValueError as exc:
            print(f"{exc}\nTip: set GEMINI_API_KEY in .env or use --dry-run")
            return 1
        except Exception as exc:
            print(f"API error: {exc}\nTip: use --dry-run")
            return 1

    print()
    print_benchmark(results)

    if dry_run and len(strategies) > 1:
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
