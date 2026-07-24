"""
Prompt assembly for Series 2.5 long-term memory lab.
"""

from __future__ import annotations

from typing import Any


def build_memory_prompt(question: str, memory_context: str) -> str:
    """
    Build prompt with injected long-term memory context.

    Only retrieved / selected memories are included — not all 500 conversations.
    """
    return f"""You are an AI engineering assistant with access to long-term user memory.

Use the memory context below to personalize your answer.

Long-Term Memory Context:
{memory_context}

User Request:
{question}

Provide:
- Direct answer personalized to the user's preferences and standards
- Supporting evidence from memory
- Engineering takeaway
"""
