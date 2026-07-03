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
    ANTI-PATTERN — no token pruning (Series 2.1 Flow 1).

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
    BEST PRACTICE — pruned context (Series 2.1 Flow 2).

    Sends only what prune.py distilled:
      - block ID, error/warning counts
      - top 10 relevant messages (not all 2000 lines)
      - one-line summary

    Same instructions to the model, ~99% fewer input tokens.
    """
    # FORMAT — numbered top messages for readable evidence block
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


def build_dynamic_prompt(user_question: str, evidence: dict[str, Any]) -> str:
    """
    DYNAMIC PROMPT — user question + runtime evidence (Series 2.2).

    This is the per-request half of the prompt. It MUST change every call
    because the question and log evidence are different each time.

    Series 2.1 already shrunk the evidence (prune.py). This function only
    formats that evidence — it does not cache anything.

    NEVER put this text in PromptCache.
    """
    # Turn the evidence list into numbered lines for the model to read
    top_messages = evidence.get("top_messages", [])
    numbered = "\n".join(f"  {i}. {msg}" for i, msg in enumerate(top_messages, 1))

    return f"""User question:
{user_question}

Runtime evidence (filtered logs):
- Block ID: {evidence.get("block_id", "unknown")}
- Relevant log count: {evidence.get("relevant_log_count", 0)}
- Error count: {evidence.get("error_count", 0)}
- Warning count: {evidence.get("warning_count", 0)}
- Top relevant messages:
{numbered}

Summary:
{evidence.get("summary", "")}"""


def build_full_prompt(static_prompt: str, dynamic_prompt: str) -> str:
    """
    PROMPT ASSEMBLY — join static + dynamic before sending to Gemini.

    Even when caching is enabled, the API still receives the full text for
    this demo. Savings are shown in token *accounting*, not by omitting text.
    """
    return f"{static_prompt.strip()}\n\n{dynamic_prompt.strip()}"
