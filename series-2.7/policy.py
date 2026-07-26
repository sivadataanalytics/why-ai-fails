"""
Security policy and budget rules for Series 2.7 model routing.

Public requests may use external models.
Confidential / restricted code must stay on internal models.
"""

from __future__ import annotations

from typing import Any

from models import MODELS

SECURITY_LEVELS = ("public", "internal", "restricted")

# Budget cap per request (USD) — dynamic router respects this when possible
DEFAULT_BUDGET_USD = 0.004


def allowed_models(security_level: str) -> set[str]:
    """Return model IDs permitted for a security classification."""
    if security_level == "public":
        return {mid for mid, m in MODELS.items() if not m["internal_only"]}
    if security_level == "internal":
        return set(MODELS.keys())
    # restricted — internal models only; large_general disallowed
    return {mid for mid, m in MODELS.items() if m["internal_only"]}


def apply_security_policy(
    candidate_model_id: str,
    security_level: str,
) -> str:
    """
    Enforce security routing policy.

    Public     → external models preferred (candidate kept if external)
    Internal   → any model
    Restricted → internal models only; escalate to internal coding tier if needed
    """
    allowed = allowed_models(security_level)
    if candidate_model_id in allowed:
        return candidate_model_id

    if security_level == "restricted":
        if "medium_coding_internal" in allowed:
            return "medium_coding_internal"
        return next(iter(allowed), "medium_coding_internal")

    # Fallback for disallowed external on internal-only paths
    return "large_general" if "large_general" in allowed else candidate_model_id


def within_budget(estimated_cost: float, budget: float = DEFAULT_BUDGET_USD) -> bool:
    return estimated_cost <= budget


def policy_metadata(security_level: str) -> dict[str, Any]:
    return {
        "security_level": security_level,
        "allowed_models": sorted(allowed_models(security_level)),
        "budget_usd": DEFAULT_BUDGET_USD,
    }
