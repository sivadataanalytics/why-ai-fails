"""
Model pool for Series 2.7 — simulated enterprise LLM catalog.

Each model exposes cost, latency, quality, and capability metadata used by the router.
"""

from __future__ import annotations

from typing import Any

# USD per 1 million tokens (demo pricing — relative tiers matter for benchmark)
MODELS: dict[str, dict[str, Any]] = {
    "small": {
        "model_id": "small",
        "name": "Small Language Model",
        "input_cost_per_m": 0.100,
        "output_cost_per_m": 0.400,
        "latency_base_sec": 0.85,
        "latency_per_1k_prompt_sec": 0.08,
        "quality_score": 0.88,
        "internal_only": False,
        "strengths": ["translation", "classification", "email_summarization"],
        "weaknesses": ["architecture_design", "legal_analysis", "reasoning"],
    },
    "medium_coding": {
        "model_id": "medium_coding",
        "name": "Medium Coding Model",
        "input_cost_per_m": 0.500,
        "output_cost_per_m": 2.000,
        "latency_base_sec": 1.40,
        "latency_per_1k_prompt_sec": 0.12,
        "quality_score": 0.93,
        "internal_only": False,
        "strengths": ["sql_generation", "backend_api", "code_review"],
        "weaknesses": ["vision", "legal_analysis"],
    },
    "medium_coding_internal": {
        "model_id": "medium_coding_internal",
        "name": "Medium Coding Model (Internal)",
        "input_cost_per_m": 0.450,
        "output_cost_per_m": 1.800,
        "latency_base_sec": 1.55,
        "latency_per_1k_prompt_sec": 0.12,
        "quality_score": 0.92,
        "internal_only": True,
        "strengths": ["sql_generation", "backend_api", "code_review"],
        "weaknesses": ["vision", "legal_analysis"],
    },
    "large_reasoning": {
        "model_id": "large_reasoning",
        "name": "Large Reasoning Model",
        "input_cost_per_m": 1.500,
        "output_cost_per_m": 6.000,
        "latency_base_sec": 2.60,
        "latency_per_1k_prompt_sec": 0.18,
        "quality_score": 0.98,
        "internal_only": False,
        "strengths": ["architecture_design", "reasoning", "legal_analysis"],
        "weaknesses": ["translation", "classification"],
    },
    "vision": {
        "model_id": "vision",
        "name": "Vision Model",
        "input_cost_per_m": 1.000,
        "output_cost_per_m": 4.000,
        "latency_base_sec": 1.90,
        "latency_per_1k_prompt_sec": 0.15,
        "quality_score": 0.94,
        "internal_only": False,
        "strengths": ["vision"],
        "weaknesses": ["sql_generation", "legal_analysis"],
    },
    "large_general": {
        "model_id": "large_general",
        "name": "Large General LLM",
        "input_cost_per_m": 3.000,
        "output_cost_per_m": 10.000,
        "latency_base_sec": 3.20,
        "latency_per_1k_prompt_sec": 0.22,
        "quality_score": 0.99,
        "internal_only": False,
        "strengths": ["all"],
        "weaknesses": [],
    },
}

SINGLE_MODEL_ID = "large_general"

MODEL_IDS = list(MODELS.keys())


def get_model(model_id: str) -> dict[str, Any]:
    if model_id not in MODELS:
        raise ValueError(f"Unknown model: {model_id}")
    return MODELS[model_id]


def estimate_model_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Estimate request cost for a specific model tier."""
    m = get_model(model_id)
    input_cost = prompt_tokens * m["input_cost_per_m"] / 1_000_000
    output_cost = completion_tokens * m["output_cost_per_m"] / 1_000_000
    return round(input_cost + output_cost, 6)


def estimate_model_latency(model_id: str, prompt_tokens: int) -> float:
    """Estimate latency from model profile and prompt size."""
    m = get_model(model_id)
    return round(
        m["latency_base_sec"] + (prompt_tokens / 1000) * m["latency_per_1k_prompt_sec"],
        2,
    )


def model_supports_task(model_id: str, task_type: str) -> bool:
    """True if model lists task_type in strengths or is general-purpose."""
    strengths = get_model(model_id)["strengths"]
    return "all" in strengths or task_type in strengths
