"""
Google Gemini client — measures real token usage from API response.

Every generate() call returns prompt_tokens from usage_metadata.
This is how we prove pruning works: same model, fewer prompt_tokens billed.
"""

from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import types

from common.config import DEFAULT_MODEL, get_api_key
from common.token_usage import estimate_tokens


def generate(prompt: str, model: str | None = None, temperature: float = 0.2) -> dict[str, Any]:
    """
    Call Gemini and return billed token counts.

    prompt_tokens     — what you pay for on input (this is what pruning reduces)
    completion_tokens — model output tokens
    total_tokens      — prompt + completion
    latency_seconds   — wall-clock time (larger prompts = slower)
    """
    client = genai.Client(api_key=get_api_key())
    model_name = model or DEFAULT_MODEL

    start = time.perf_counter()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    latency_seconds = round(time.perf_counter() - start, 2)

    # usage_metadata comes from Gemini — real billed token counts, not estimates
    usage = response.usage_metadata
    prompt_tokens = getattr(usage, "prompt_token_count", None) or estimate_tokens(prompt)
    completion_tokens = getattr(usage, "candidates_token_count", None) or estimate_tokens(
        response.text or ""
    )
    total_tokens = getattr(usage, "total_token_count", None) or (
        prompt_tokens + completion_tokens
    )

    return {
        "text": (response.text or "").strip(),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "total_tokens": int(total_tokens),
        "latency_seconds": latency_seconds,
        "model": model_name,
    }
