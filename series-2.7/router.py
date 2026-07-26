"""
Model routing strategies for Series 2.7.

Pipeline:
  User Request → Intent → Classification → Complexity → Cost → Policy → Model

Strategies:
  single     — baseline: everything to large general model
  rules      — static task-type → model mapping
  dynamic    — score models on intent, complexity, cost, latency, policy
  confidence — start cheap; escalate to larger model when confidence is low
"""

from __future__ import annotations

from typing import Any

from classifier import classify_task, classification_confidence
from complexity import complexity_score, estimate_complexity
from models import (
    MODELS,
    SINGLE_MODEL_ID,
    estimate_model_cost,
    estimate_model_latency,
    get_model,
    model_supports_task,
)
from policy import apply_security_policy, allowed_models

STRATEGIES = ("single", "rules", "dynamic", "confidence")

STRATEGY_NAMES = {
    "single": "SINGLE MODEL",
    "rules": "RULE ROUTING",
    "dynamic": "DYNAMIC ROUTING",
    "confidence": "CONFIDENCE ROUTING",
}

# Rule-based routing table (Strategy 2)
RULE_MAP: dict[str, str] = {
    "translation": "small",
    "email_summarization": "small",
    "classification": "small",
    "sql_generation": "medium_coding",
    "backend_api": "medium_coding",
    "code_review": "medium_coding",
    "vision": "vision",
    "architecture_design": "large_reasoning",
    "legal_analysis": "large_reasoning",
    "reasoning": "large_reasoning",
}

CONFIDENCE_THRESHOLD = 0.72

# One-step escalation map (confidence routing — escalate only one tier)
ESCALATION_STEP: dict[str, str] = {
    "small": "medium_coding",
    "medium_coding": "large_reasoning",
    "medium_coding_internal": "large_reasoning",
    "vision": "large_reasoning",
    "large_reasoning": "large_general",
}


def _completion_tokens(complexity: str) -> int:
    return {"simple": 80, "medium": 160, "complex": 320}[complexity]


def _route_single(_request: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
    """Strategy 1 — everything to the large general model."""
    return {
        "model_id": SINGLE_MODEL_ID,
        "escalated": False,
        "confidence": 1.0,
        "reason": "single_model_baseline",
    }


def _route_rules(request: dict[str, Any], *, task_type: str, **_kwargs: Any) -> dict[str, Any]:
    """Strategy 2 — fixed rules by task type (prompt-only classification may mis-route)."""
    model_id = RULE_MAP.get(task_type, "large_reasoning")
    model_id = apply_security_policy(model_id, request["security_level"])
    return {
        "model_id": model_id,
        "escalated": False,
        "confidence": 0.85,
        "reason": f"rule:{task_type}",
    }


def _score_model(
    model_id: str,
    *,
    task_type: str,
    complexity: str,
    prompt_tokens: int,
    security_level: str,
) -> float:
    """Higher score = better fit for dynamic routing."""
    m = get_model(model_id)
    if model_id not in allowed_models(security_level):
        return -1.0

    support = 1.0 if model_supports_task(model_id, task_type) else 0.35
    quality = m["quality_score"]
    comp = complexity_score(complexity)

    # Prefer right-sized models: penalize overkill
    tier_penalty = 0.0
    if complexity == "simple" and model_id in ("large_general", "large_reasoning"):
        tier_penalty = 0.35
    if complexity == "complex" and model_id == "small":
        tier_penalty = 0.50

    completion = _completion_tokens(complexity)
    cost = estimate_model_cost(model_id, prompt_tokens, completion)
    latency = estimate_model_latency(model_id, prompt_tokens)

    # Normalize cost/latency into score penalties (lower is better)
    cost_penalty = min(0.35, cost * 80)
    latency_penalty = min(0.25, latency * 0.06)

    return (
        0.40 * support
        + 0.30 * quality
        + 0.20 * (1.0 - abs(comp - quality))
        - tier_penalty
        - cost_penalty
        - latency_penalty
    )


def _route_dynamic(
    request: dict[str, Any],
    *,
    task_type: str,
    complexity: str,
    prompt_tokens: int,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Strategy 3 — pick highest-scoring allowed model."""
    security = request["security_level"]
    candidates = [mid for mid in MODELS if mid != "large_general" or complexity == "complex"]
    scored = [
        (_score_model(mid, task_type=task_type, complexity=complexity,
                      prompt_tokens=prompt_tokens, security_level=security), mid)
        for mid in candidates
    ]
    scored = [(s, mid) for s, mid in scored if s >= 0]
    scored.sort(reverse=True)
    model_id = scored[0][1] if scored else SINGLE_MODEL_ID
    model_id = apply_security_policy(model_id, security)
    return {
        "model_id": model_id,
        "escalated": False,
        "confidence": round(min(0.98, scored[0][0] + 0.35), 2) if scored else 0.5,
        "reason": "dynamic:best_score",
    }


def _route_confidence(
    request: dict[str, Any],
    *,
    task_type: str,
    complexity: str,
    prompt_tokens: int,
    **_kwargs: Any,
) -> dict[str, Any]:
    """
    Strategy 4 — route to rule-based tier first; escalate one step if confidence is low.

    Simulates: primary model → confidence check → optional single escalation.
    """
    security = request["security_level"]
    allowed = allowed_models(security)

    primary = RULE_MAP.get(task_type, "small")
    primary = apply_security_policy(primary, security)
    confidence = classification_confidence(request["prompt"], task_type)

    if model_supports_task(primary, task_type):
        confidence += 0.12
    else:
        confidence -= 0.10

    chosen = primary
    escalated = False

    should_escalate = (
        (complexity == "complex" and confidence < 0.78)
        or not model_supports_task(primary, task_type)
    )

    if should_escalate:
        if primary == "large_reasoning":
            next_model = "large_general"
        else:
            next_model = ESCALATION_STEP.get(primary, "large_reasoning")
        next_model = apply_security_policy(next_model, security)
        if next_model in allowed and next_model != primary:
            chosen = next_model
            escalated = True
            confidence = min(0.99, confidence + 0.20)

    return {
        "model_id": chosen,
        "escalated": escalated,
        "confidence": round(min(0.99, max(0.45, confidence)), 2),
        "reason": "confidence:escalated" if escalated else "confidence:accepted",
    }


def analyze_request(request: dict[str, Any], *, use_metadata: bool = False) -> dict[str, Any]:
    """Run intent, complexity, and context analysis for one request."""
    hint = request.get("task_type") if use_metadata else None
    task_type = classify_task(request["prompt"], hint=hint)
    complexity = estimate_complexity(
        request["prompt"],
        task_type=task_type,
        context_tokens=request.get("context_tokens", 0),
    )
    prompt_tokens = request.get("context_tokens", 0) + max(20, len(request["prompt"]) // 4)
    return {
        "task_type": task_type,
        "complexity": complexity,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": _completion_tokens(complexity),
    }


def route_request(request: dict[str, Any], strategy: str, *, dry_run: bool = True) -> dict[str, Any]:
    """Route one request; call Gemini when dry_run=False."""
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")

    use_metadata = strategy in ("dynamic", "confidence")
    analysis = analyze_request(request, use_metadata=use_metadata)
    task_type = analysis["task_type"]
    complexity = analysis["complexity"]
    prompt_tokens = analysis["prompt_tokens"]
    completion_tokens = analysis["completion_tokens"]

    routers = {
        "single": _route_single,
        "rules": _route_rules,
        "dynamic": _route_dynamic,
        "confidence": _route_confidence,
    }
    decision = routers[strategy](
        request,
        task_type=task_type,
        complexity=complexity,
        prompt_tokens=prompt_tokens,
    )

    model_id = decision["model_id"]
    result: dict[str, Any] = {
        **analysis,
        **decision,
        "strategy": strategy,
        "model_name": get_model(model_id)["name"],
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cost": estimate_model_cost(model_id, prompt_tokens, completion_tokens),
        "latency_seconds": estimate_model_latency(model_id, prompt_tokens),
        "expected_model": request["expected_model"],
        "request_id": request["request_id"],
        "response_text": "",
    }

    if dry_run:
        return result

    from common.gemini_client import generate
    from prompts import build_routing_prompt

    prompt = build_routing_prompt(request, result)
    api = generate(prompt)
    result["response_text"] = api["text"]
    result["prompt_tokens"] = api["prompt_tokens"]
    result["completion_tokens"] = api["completion_tokens"]
    result["total_tokens"] = api["total_tokens"]
    result["latency_seconds"] = api["latency_seconds"]
    result["estimated_cost"] = estimate_model_cost(
        model_id, api["prompt_tokens"], api["completion_tokens"]
    )
    return result
