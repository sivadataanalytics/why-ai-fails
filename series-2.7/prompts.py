"""
Prompt template for Series 2.7 live Gemini routing demo.
"""

from __future__ import annotations

from typing import Any


def build_routing_prompt(request: dict[str, Any], routing: dict[str, Any]) -> str:
    """Build prompt sent to Gemini when executing a routed request live."""
    return f"""You are an enterprise AI assistant. Respond concisely and accurately.

Task type: {routing.get('task_type', request.get('task_type', 'general'))}
Complexity: {routing.get('complexity', request.get('complexity', 'medium'))}
Routed model tier: {routing.get('model_name', 'unknown')}

User request:
{request['prompt']}

Provide a helpful, professional response."""
