"""
Multi-agent orchestrator for Series 2.8.

Four strategies:
  single     — one general agent handles entire request
  sequential — planner → specialized agents in dependency order
  parallel   — planner → parallel waves by dependency graph
  reviewer   — parallel execution + reviewer + one rework iteration

Pipeline:
  User Request → Planner → Scheduler → Agents → Shared Memory
  → Aggregator → (Reviewer) → Final Response
"""

from __future__ import annotations

from typing import Any

from agents import SINGLE_AGENT, SINGLE_AGENT_ID, get_agent, simulate_agent_output
from common.token_usage import estimate_cost, estimate_tokens
from evaluator import consistency_score, overall_quality, security_score, task_completion
from planner import plan_request
from reviewer import apply_rework, review
from scheduler import schedule, total_scheduled_latency, wave_latency_seconds
from shared_memory import SharedMemory

STRATEGIES = ("single", "sequential", "parallel", "reviewer")

STRATEGY_NAMES = {
    "single": "SINGLE AGENT",
    "sequential": "SEQUENTIAL",
    "parallel": "PARALLEL",
    "reviewer": "PARALLEL + REVIEWER",
}


def orchestrate(request: dict[str, Any], strategy: str, *, dry_run: bool = True) -> dict[str, Any]:
    """Run full orchestration for one request and one strategy."""
    if strategy == "single":
        return _run_single(request, dry_run=dry_run)
    if strategy == "sequential":
        return _run_multi(request, schedule_mode="sequential", with_reviewer=False, dry_run=dry_run)
    if strategy == "parallel":
        return _run_multi(request, schedule_mode="parallel", with_reviewer=False, dry_run=dry_run)
    if strategy == "reviewer":
        return _run_multi(request, schedule_mode="parallel", with_reviewer=True, dry_run=dry_run)
    raise ValueError(f"Unknown strategy: {strategy}")


def _run_single(request: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    """Strategy 1 — everything to one general-purpose agent."""
    memory = SharedMemory(request)
    prompt = request["prompt"]
    output_text = (
        f"# General Solution\n\n"
        f"Single-agent response for: {prompt}\n\n"
        f"- High-level architecture outline\n"
        f"- Partial API sketch\n"
        f"- Limited security and testing depth\n"
    )
    prompt_tokens = estimate_tokens(prompt) + SINGLE_AGENT["prompt_overhead"]
    completion_tokens = SINGLE_AGENT["output_tokens"]
    latency = SINGLE_AGENT["base_latency"]

    agent_results = [{
        "agent_id": SINGLE_AGENT_ID,
        "agent_name": SINGLE_AGENT["name"],
        "domain": "general",
        "output_text": output_text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_seconds": latency,
        "quality_factor": 0.78,
    }]
    memory.write("general", {"summary": output_text[:500], "full_text": output_text}, agent_id=SINGLE_AGENT_ID)
    # Single agent produces shallow coverage — not full domain separation
    for domain in ("architecture", "backend", "database", "documentation"):
        memory.write(domain, {
            "summary": f"Shallow {domain} outline (single-agent, not specialized)",
            "quality_factor": 0.70,
        }, agent_id=SINGLE_AGENT_ID)
    aggregated = memory.aggregate()

    completion = task_completion(memory.keys(), request.get("required_domains"))
    consistency = 0.76
    sec = 0.82 if request.get("security_level") == "restricted" else 0.78
    quality = 0.84

    return _build_result(
        request=request,
        strategy="single",
        memory=memory,
        agent_results=agent_results,
        aggregated=aggregated,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency=latency,
        task_completion=completion,
        consistency=consistency,
        security=sec,
        review_score=None,
        overall_quality=quality,
        review_iterations=0,
        rework_count=0,
        dry_run=dry_run,
    )


def _run_multi(
    request: dict[str, Any],
    *,
    schedule_mode: str,
    with_reviewer: bool,
    dry_run: bool,
) -> dict[str, Any]:
    """Strategies 2–4 — planner + scheduled specialized agents."""
    memory = SharedMemory(request)
    plan = plan_request(request)
    memory.write("plan", {"summary": plan["plan_text"], "tasks": plan["tasks"]}, agent_id="planner")

    tasks = plan["tasks"]
    waves = schedule(tasks, mode=schedule_mode)

    agent_results: list[dict[str, Any]] = []
    planner_result = simulate_agent_output("planner", request, memory.snapshot())
    agent_results.append(planner_result)

    from agents import AGENTS as AGENT_MAP
    agent_latencies = {aid: meta.get("base_latency", 1.0) for aid, meta in AGENT_MAP.items()}

    total_latency = 0.0
    prompt_tokens = planner_result["prompt_tokens"]
    completion_tokens = planner_result["completion_tokens"]

    for wave in waves:
        wave_lat = wave_latency_seconds(wave, agent_latencies)
        total_latency += wave_lat + 0.15
        for task in wave:
            result = simulate_agent_output(task["agent_id"], request, memory.snapshot())
            memory.write_agent_output(result)
            agent_results.append(result)
            prompt_tokens += result["prompt_tokens"]
            completion_tokens += result["completion_tokens"]

    review_iterations = 0
    rework_count = 0
    review_score: float | None = None

    if with_reviewer:
        review_result = review(memory, request=request)
        review_iterations = 1
        review_score = review_result["review_score"]
        total_latency += get_agent("reviewer")["base_latency"] + 0.8
        prompt_tokens += 500
        completion_tokens += 200
        if review_result.get("rework_agents"):
            rework = apply_rework(memory, request, review_result["rework_agents"])
            rework_count = len(rework)
            for r in rework:
                agent_results.append(r)
                prompt_tokens += r["prompt_tokens"]
                completion_tokens += r["completion_tokens"]
                total_latency += r["latency_seconds"]
            # Re-review after rework (light pass — score boost)
            review_result = review(memory, request=request)
            review_score = max(review_score or 0, review_result["review_score"])

    aggregated = memory.aggregate()
    if schedule_mode == "sequential":
        total_latency = total_scheduled_latency(waves, agent_latencies) * 1.55
    else:
        total_latency = round(total_latency * 1.05, 2)

    completion = task_completion(memory.keys(), request.get("required_domains"))
    consistency = consistency_score(agent_results)
    sec = security_score({"request": request, "memory_keys": memory.keys(), "review": memory.read("review")})
    strategy_key = "reviewer" if with_reviewer else schedule_mode
    quality = overall_quality(
        completion=completion,
        consistency=consistency,
        security=sec,
        review=review_score,
        strategy=strategy_key,
    )

    return _build_result(
        request=request,
        strategy=strategy_key,
        memory=memory,
        agent_results=agent_results,
        aggregated=aggregated,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency=total_latency,
        task_completion=completion,
        consistency=consistency,
        security=sec,
        review_score=review_score,
        overall_quality=quality,
        review_iterations=review_iterations,
        rework_count=rework_count,
        dry_run=dry_run,
    )


def _build_result(
    *,
    request: dict[str, Any],
    strategy: str,
    memory: SharedMemory,
    agent_results: list[dict[str, Any]],
    aggregated: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency: float,
    task_completion: float,
    consistency: float,
    security: float,
    review_score: float | None,
    overall_quality: float,
    review_iterations: int,
    rework_count: int,
    dry_run: bool,
) -> dict[str, Any]:
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    return {
        "request_id": request["request_id"],
        "request": request,
        "strategy": strategy,
        "strategy_name": STRATEGY_NAMES[strategy],
        "dry_run": dry_run,
        "agent_results": agent_results,
        "memory_keys": memory.keys(),
        "aggregated_solution": aggregated,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_seconds": round(latency, 2),
        "estimated_cost": cost,
        "task_completion": task_completion,
        "consistency_score": consistency,
        "security_score": security,
        "review_score": review_score,
        "overall_quality": overall_quality,
        "review_iterations": review_iterations,
        "rework_count": rework_count,
    }
