# Build prompts for the two demo flows (bloated vs pruned)

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
    # Intentionally includes entire log dump — simulates a naive integration
    return f"""You are an HDFS incident investigation assistant.

User question:
{user_question}

Here are the logs:
{raw_logs}

{INSTRUCTIONS}"""


def build_pruned_prompt(user_question: str, evidence: dict[str, Any]) -> str:
    # Only block-scoped summary and top messages — minimal token footprint
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
