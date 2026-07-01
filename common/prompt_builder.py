"""
Prompt builders — where token pruning becomes visible.

Two prompts, same question, wildly different token counts:

  build_unpruned_prompt()  →  embeds ALL raw log lines     (~71,000 tokens)
  build_pruned_prompt()    →  embeds evidence summary only (~200 tokens)

The LLM task is identical. Only the context size changes.
That is the entire point of context pruning.
"""

from __future__ import annotations

from typing import Any

INSTRUCTIONS = """
Please provide:
- likely root cause
- affected component
- supporting evidence
- recommended next action
""".strip()


def build_unpruned_prompt(user_question: str, raw_logs: str) -> str:
    """
    ANTI-PATTERN — no token pruning.

    Concatenates the entire log file into the prompt string.
    Every log line becomes billable input tokens, including lines
    about unrelated blocks, healthy nodes, and routine INFO messages.

    Use this flow only to demonstrate the cost of NOT pruning.
    """
    return f"""You are an HDFS incident investigation assistant.

User question:
{user_question}

Here are the logs:
{raw_logs}

{INSTRUCTIONS}"""


def build_pruned_prompt(user_question: str, evidence: dict[str, Any]) -> str:
    """
    BEST PRACTICE — pruned context.

    Sends only what prune.py distilled:
      - block ID, error/warning counts
      - top 10 relevant messages (not all 2000 lines)
      - one-line summary

    Same instructions to the model, ~99% fewer input tokens.
    """
    top_messages = evidence.get("top_messages", [])
    numbered = "\n".join(f"  {i}. {msg}" for i, msg in enumerate(top_messages, 1))

    return f"""You are an HDFS incident investigation assistant.

User question:
{user_question}

Pruned evidence:
- Block ID: {evidence.get("block_id", "unknown")}
- Relevant log count: {evidence.get("relevant_log_count", 0)}
- Error count: {evidence.get("error_count", 0)}
- Warning count: {evidence.get("warning_count", 0)}
- Top relevant messages:
{numbered}

Summary:
{evidence.get("summary", "")}

{INSTRUCTIONS}"""
