"""
Series 2.7 — Model Routing Engineering Lab (start reading here).

Live mode calls Gemini for each routed request. Dry-run uses routing metadata only.

RUN
---
  python series-2.7/app.py --dry-run
  python series-2.7/app.py --live --live-limit 5
  python series-2.7/app.py --live --request-id r0025
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
from requests import REQUESTS, REQUESTS_BY_ID, generate_requests
from router import STRATEGIES, STRATEGY_NAMES, route_request

DEFAULT_STRATEGIES = list(STRATEGIES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Model routing benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Route only; no Gemini calls")
    parser.add_argument("--live", action="store_true", help="Call Gemini for each routed request")
    parser.add_argument("--strategy", choices=list(STRATEGIES))
    parser.add_argument("--request-id", choices=list(REQUESTS_BY_ID.keys()))
    parser.add_argument("--requests", type=int, default=len(REQUESTS), help="Dataset size")
    parser.add_argument(
        "--live-limit",
        type=int,
        default=5,
        help="Max live Gemini calls per strategy when --live (default 5)",
    )
    args = parser.parse_args(argv)

    dry_run = not args.live
    if args.dry_run and args.live:
        print("Use either --dry-run or --live, not both.")
        return 1

    load_config()

    requests = generate_requests(args.requests) if args.requests != len(REQUESTS) else REQUESTS
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(requests):,} AI requests")
    print(f"Strategies: {', '.join(strategies)}")
    if dry_run:
        print("Mode: dry-run (routing metadata only)\n")
    else:
        print(f"Mode: live (Gemini per request, up to {args.live_limit} per strategy)\n")

    if args.request_id:
        req = REQUESTS_BY_ID.get(args.request_id) or requests[0]
        for strategy in strategies:
            routing = route_request(req, strategy, dry_run=dry_run)
            print(f"--- {STRATEGY_NAMES[strategy]} / {req['request_id']} ---")
            print(f"Task        : {routing['task_type']}")
            print(f"Complexity  : {routing['complexity']}")
            print(f"Security    : {req['security_level']}")
            print(f"Model       : {routing['model_name']} ({routing['model_id']})")
            print(f"Expected    : {routing['expected_model']}")
            print(f"Cost        : ${routing['estimated_cost']:.4f}")
            print(f"Latency     : {routing['latency_seconds']} sec")
            print(f"Escalated   : {routing.get('escalated', False)}")
            print(f"Reason      : {routing.get('reason', '')}")
            if routing.get("response_text"):
                print("\n--- Answer excerpt ---")
                print(routing["response_text"][:400])
            print()
        return 0

    live_requests = requests[: args.live_limit] if not dry_run else requests
    if not dry_run and args.live_limit < len(requests):
        print(
            f"Live limit: {len(live_requests)} of {len(requests)} requests "
            f"(each invokes one Gemini call)\n"
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

    if len(strategies) > 1:
        print("\n--- Routing accuracy detail ---")
        for r in results:
            print(
                f"{r['strategy_name']}: accuracy={r['accuracy']} "
                f"avg_cost=${r['avg_cost']:.4f} "
                f"escalation={r.get('escalation_rate', 0):.0%}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
