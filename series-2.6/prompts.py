"""
Prompt assembly for Series 2.6 memory retrieval lab.
"""

from __future__ import annotations

from typing import Any


def build_retrieval_prompt(query: str, retrieved: list[dict[str, Any]]) -> str:
    """
    Build prompt with only top-K retrieved memories — not the full 100k store.
    """
    if retrieved:
        blocks = []
        for mem in retrieved:
            blocks.append(
                f"- [{mem['category']}] {mem['text']} "
                f"(confidence={mem['confidence']}, recency={mem['recency']})"
            )
        memory_block = "\n".join(blocks)
    else:
        memory_block = "(no memories retrieved)"

    return f"""You are an AI engineering assistant with access to retrieved long-term user memory.

Use ONLY the retrieved memories below to personalize your answer.

Retrieved Memories:
{memory_block}

User Request:
{query}

Provide:
- Direct personalized answer
- Supporting evidence from retrieved memories
- Engineering takeaway
"""
