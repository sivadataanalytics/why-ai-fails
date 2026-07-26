"""
Prompt templates for live Gemini runs in Series 2.8.

Dry-run uses simulated agent outputs; live mode sends aggregated context.
"""

from __future__ import annotations

from typing import Any


def build_orchestration_prompt(request: dict[str, Any], run: dict[str, Any]) -> str:
    """Prompt for live Gemini — final aggregated multi-agent solution."""
    strategy = run.get("strategy_name", run.get("strategy", ""))
    aggregated = run.get("aggregated_solution", "")
    return f"""You are an enterprise software engineering assistant.

Strategy: {strategy}
Request: {request['prompt']}
Category: {request.get('category', 'general')}

Multi-agent outputs (aggregated):
{aggregated[:6000]}

Provide a concise executive summary:
1. Architecture highlights
2. Key deliverables completed
3. Security considerations
4. Recommended next steps
"""


def build_single_agent_prompt(request: dict[str, Any]) -> str:
    return f"""You are a general-purpose enterprise software architect.

Request: {request['prompt']}

Provide a high-level solution covering architecture, backend, frontend,
database, security, testing, and deployment in one response.
Keep it under 800 words.
"""
