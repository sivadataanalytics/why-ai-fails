"""
Gemini prompts and prompt assembly for Series 2.4.

Two prompt shapes:

  FULL strategy:
    User Question + Full Conversation History (all 178 messages)

  All other strategies:
    User Question + Conversation Memory + Latest Messages

Gemini never sees the full conversation except in the full baseline strategy.
"""

from __future__ import annotations

from typing import Any


def build_answer_prompt(
    question: str,
    *,
    memory_text: str,
    latest_messages: list[dict[str, Any]],
    strategy_key: str,
) -> str:
    """
    Assemble the prompt sent to Gemini (or estimated in --dry-run).

    Parameters
    ----------
    question        : benchmark question (e.g. "What language does the user prefer?")
    memory_text     : compressed summary (empty for 'full' strategy)
    latest_messages : recent verbatim messages (or ALL messages for 'full')
    strategy_key    : determines prompt shape
    """
    if strategy_key == "full":
        # BASELINE — entire conversation in prompt (expensive, perfect memory)
        history = "\n\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in latest_messages
        )
        context_section = f"Full Conversation History ({len(latest_messages)} messages):\n{history}"
    else:
        # SUMMARIZED — memory block + small recent window (cheap, preserved facts)
        recent = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in latest_messages
        )
        context_section = f"""Conversation Memory:
{memory_text}

Latest Messages:
{recent}"""

    return f"""You are an AI engineering assistant helping evaluate conversation memory.

Answer the user question using ONLY the conversation context below.

{context_section}

User Question:
{question}

Provide:
- Direct answer
- Supporting evidence from the context
- Engineering takeaway
"""


# Template for future LLM-based summarization (not used in dry-run lab)
SUMMARIZE_PROMPT_TEMPLATE = """Summarize the following conversation segment.
Keep: preferences, project, architecture decisions, pending tasks, constraints.
Discard: greetings, thanks, small talk, repeated resolved issues.

Conversation segment:
{segment}

Output a concise bullet summary.
"""
