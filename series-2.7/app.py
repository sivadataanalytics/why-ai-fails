"""
Series 2.7 — Model Routing Engineering Lab (start reading here).

WHAT THIS DEMO PROVES
---------------------
Enterprise AI systems become efficient by selecting the right model — not the
biggest model on every request.

1,000 AI requests → intent + complexity + policy → model router → simulated execution

ARCHITECTURE
------------
  User Request
        ↓
  Intent Detection + Task Classification
        ↓
  Complexity Estimation
        ↓
  Cost Evaluation + Security Policy
        ↓
  Model Router (single / rules / dynamic / confidence)
        ↓
  Best Model → Gemini (live) or simulation (dry-run)

READING ORDER
-------------
1. models.py      — model pool (cost, latency, strengths)
2. requests.py    — 1,000 synthetic requests
3. classifier.py  — intent detection
4. router.py      — four routing strategies
5. evaluator.py   — accuracy, utilization, escalation
6. app.py main()  — benchmark flow

RUN
---
  python series-2.7/app.py --dry-run
  python series-2.7/app.py --strategy confidence --dry-run
  python series-2.7/app.py --request-id r0025
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
from prompts import build_routing_prompt
from requests import DEFAULT_REQUEST_ID, REQUESTS, REQUESTS_BY_ID, generate_requests
from router import STRATEGIES, STRATEGY_NAMES, route_request

DEFAULT_STRATEGIES = list(STRATEGIES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Model routing benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Simulate routing; no Gemini calls")
    parser.add_argument("--strategy", choices=list(STRATEGIES))
    parser.add_argument("--request-id", choices=list(REQUESTS_BY_ID.keys()))
    parser.add_argument("--requests", type=int, default=len(REQUESTS), help="Dataset size")
    args = parser.parse_args(argv)

    load_config()

    requests = generate_requests(args.requests) if args.requests != len(REQUESTS) else REQUESTS
    strategies = [args.strategy] if args.strategy else DEFAULT_STRATEGIES

    print(f"Loaded {len(requests):,} AI requests")
    print(f"Strategies: {', '.join(strategies)}")
    print("Mode: dry-run (simulated routing)\n" if args.dry_run else "Mode: live (Gemini for selected request)\n")

    if args.request_id:
        req = REQUESTS_BY_ID.get(args.request_id) or requests[0]
        for strategy in strategies:
            routing = route_request(req, strategy)
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
            print()

        if not args.dry_run:
            strategy = strategies[0]
            routing = route_request(req, strategy)
            from common.gemini_client import generate

            prompt = build_routing_prompt(req, routing)
            print(f"Calling Gemini ({routing['model_name']}) ...")
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
        results.append(run_strategy(strategy, requests))

    print()
    print_benchmark(results)

    if args.dry_run and len(strategies) > 1:
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
