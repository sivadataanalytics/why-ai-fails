"""
Summarization strategies for Series 2.4.

Four strategies — same conversation, same question, only summarization changes:

  Strategy 1 — FULL CONVERSATION
    Send all 178 messages. Perfect memory, highest cost.

  Strategy 2 — ROLLING SUMMARY
    Latest 10 messages verbatim + evolving summary of everything older.

  Strategy 3 — HIERARCHICAL SUMMARY
    Every 20 messages → block summary → master summary + latest 10.

  Strategy 4 — SEMANTIC SUMMARY
    Structured facts only (preferences, tasks, decisions) + latest 5.
    Discards greetings, thanks, small talk.

Summaries are built locally (no LLM) so --dry-run works without an API key.
Live mode uses the same compressed memory; Gemini only answers the benchmark question.
"""

from __future__ import annotations

from typing import Any

from common.token_usage import estimate_tokens
from memory import ConversationMemory, extract_memory

# ---------------------------------------------------------------------------
# WINDOW SIZES — how many recent messages stay verbatim in the prompt
# ---------------------------------------------------------------------------
LATEST_ROLLING = 10       # Strategy 2: recent context preserved word-for-word
LATEST_HIERARCHICAL = 10  # Strategy 3: same recent window after master summary
LATEST_SEMANTIC = 5       # Strategy 4: fewer verbatim messages (memory carries facts)
HIERARCHICAL_BLOCK = 20   # Strategy 3: messages per block before summarizing

STRATEGIES: dict[str, dict[str, Any]] = {
    "full": {"name": "FULL CONVERSATION", "key": "full"},
    "rolling": {"name": "ROLLING SUMMARY", "key": "rolling"},
    "hierarchical": {"name": "HIERARCHICAL SUMMARY", "key": "hierarchical"},
    "semantic": {"name": "SEMANTIC SUMMARY", "key": "semantic"},
}

# Phrases filtered out during compression — conversational noise, not memory
NOISE_PHRASES = (
    "thank you",
    "thanks",
    "good morning",
    "got it",
    "ok sounds good",
    "you're welcome",
    "yes, i'm here",
)


def _format_message(msg: dict[str, Any]) -> str:
    """Format one message as 'User: ...' or 'Assistant: ...'."""
    role = msg["role"].capitalize()
    return f"{role}: {msg['content']}"


def _is_low_value(content: str) -> bool:
    """
    Detect low-value messages (greetings, acknowledgments).

    Semantic strategy discards these entirely.
    Rolling/hierarchical skip them during bullet compression.
    """
    lowered = content.strip().lower()
    return any(p in lowered for p in NOISE_PHRASES) and len(lowered) < 40


def _compress_messages(messages: list[dict[str, Any]], *, label: str) -> str:
    """
    Turn a block of messages into a bullet summary.

    Skips noise phrases; truncates long lines to ~160 chars per bullet.
    Caps at 12 bullets to prevent summary bloat.
    """
    bullets: list[str] = []
    for msg in messages:
        if _is_low_value(msg["content"]):
            continue
        bullets.append(f"- [{msg['role']}] {msg['content'][:160]}")

    # Fallback: if everything was noise, keep last 3 messages anyway
    if not bullets:
        bullets = [f"- [{m['role']}] {m['content'][:100]}" for m in messages[-3:]]

    return f"{label}\n" + "\n".join(bullets[:12])


def _rolling_summary(older: list[dict[str, Any]]) -> str:
    """
    Strategy 2 — Rolling Summary of messages before the latest window.

    Two layers:
      1. Bullet compression of older turns (drops noise)
      2. Structured key facts from extract_memory() (preserves critical info)

    The summary evolves as the conversation grows — older bullets compress further.
    """
    bullets = _compress_messages(older, label="Rolling Conversation Summary:")
    if not older:
        return bullets
    key_facts = extract_memory(older).to_text()
    return f"{bullets}\n\n{key_facts}"


def _hierarchical_summary(older: list[dict[str, Any]]) -> str:
    """
    Strategy 3 — Hierarchical Summary for very long conversations.

    Flow:
      20 messages → Summary A
      20 messages → Summary B
      ...
      Summary A + B + ... → Master Summary
      + structured key facts

    Prevents one giant rolling summary from growing without bound.
    """
    blocks: list[str] = []
    for i in range(0, len(older), HIERARCHICAL_BLOCK):
        block = older[i : i + HIERARCHICAL_BLOCK]
        letter = chr(ord("A") + len(blocks))
        block_summary = _compress_messages(block, label=f"Summary {letter}:")
        blocks.append(block_summary)

    # Master summary: one line per block (high-level index)
    master_lines = ["Master Summary:"]
    for i, block in enumerate(blocks):
        first_line = block.split("\n")[1] if "\n" in block else block[:120]
        master_lines.append(f"  Block {i + 1}: {first_line[:120]}")

    key_facts = extract_memory(older).to_text()
    return "\n".join(master_lines) + f"\n\n{key_facts}"


def apply_strategy(
    messages: list[dict[str, Any]],
    strategy_key: str,
) -> dict[str, Any]:
    """
    Build conversation memory for one strategy.

    Returns
    -------
    memory_text           : compressed history (empty for 'full' strategy)
    latest_messages       : recent messages kept verbatim
    summary_size          : token count of memory_text
    message_count_in_prompt : how many raw messages go into the prompt
    """
    strategy = STRATEGIES[strategy_key]

    # --- Strategy 1: FULL — no compression, send everything ---
    if strategy_key == "full":
        memory_text = ""
        latest = messages  # all 178 messages
        return {
            "strategy_key": strategy_key,
            "strategy_name": strategy["name"],
            "memory_text": memory_text,
            "latest_messages": latest,
            "message_count_in_prompt": len(latest),
            "summary_size": 0,
        }

    # --- Strategy 2: ROLLING — summary of older + latest 10 ---
    if strategy_key == "rolling":
        latest = messages[-LATEST_ROLLING:]
        older = messages[:-LATEST_ROLLING]
        memory_text = _rolling_summary(older) if older else "Rolling Conversation Summary:\n(none yet)"
        return _pack(strategy_key, strategy["name"], memory_text, latest)

    # --- Strategy 3: HIERARCHICAL — block summaries + master + latest 10 ---
    if strategy_key == "hierarchical":
        latest = messages[-LATEST_HIERARCHICAL:]
        older = messages[:-LATEST_HIERARCHICAL]
        memory_text = _hierarchical_summary(older) if older else "Master Summary:\n(none yet)"
        return _pack(strategy_key, strategy["name"], memory_text, latest)

    # --- Strategy 4: SEMANTIC — structured facts only + latest 5 ---
    if strategy_key == "semantic":
        latest = messages[-LATEST_SEMANTIC:]
        memory: ConversationMemory = extract_memory(messages[:-LATEST_SEMANTIC])
        memory_text = memory.to_text()
        return _pack(strategy_key, strategy["name"], memory_text, latest)

    raise ValueError(f"Unknown strategy: {strategy_key}")


def _pack(
    strategy_key: str,
    strategy_name: str,
    memory_text: str,
    latest: list[dict[str, Any]],
) -> dict[str, Any]:
    """Package strategy output into a consistent dict for app.py and benchmark.py."""
    return {
        "strategy_key": strategy_key,
        "strategy_name": strategy_name,
        "memory_text": memory_text,
        "latest_messages": latest,
        "message_count_in_prompt": len(latest),
        "summary_size": estimate_tokens(memory_text),
    }
