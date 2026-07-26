"""
Prompt templates for Series 2.8 — per-agent and aggregated Gemini calls.
"""

from __future__ import annotations

import json
from typing import Any


def _format_memory(memory_snapshot: dict[str, Any]) -> str:
    """Serialize shared memory for agent context (truncate large entries)."""
    parts: list[str] = []
    for key, value in memory_snapshot.items():
        if key == "request":
            continue
        if isinstance(value, dict):
            text = value.get("summary") or value.get("full_text") or json.dumps(value)[:400]
        else:
            text = str(value)[:400]
        parts.append(f"### {key}\n{text}")
    return "\n\n".join(parts) if parts else "(no prior agent outputs yet)"


def build_agent_prompt(
    agent_id: str,
    request: dict[str, Any],
    memory_snapshot: dict[str, Any],
) -> str:
    """Prompt for one specialized agent — reads request + shared memory."""
    from agents import get_agent

    agent = get_agent(agent_id)
    memory_block = _format_memory(memory_snapshot)
    return f"""You are the {agent['name']} in an enterprise multi-agent software delivery team.

Your role: {agent.get('description', agent_id)}

Enterprise request:
{request['prompt']}

Category: {request.get('category', 'general')}
Security level: {request.get('security_level', 'standard')}

Shared memory from other agents:
{memory_block}

Produce a focused deliverable for your domain ({agent.get('domain', agent_id)}).
Use markdown headings and bullet points. Be specific and actionable (150–400 words).
"""


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
