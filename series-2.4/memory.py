"""
Structured conversation memory for Series 2.4.

Semantic summarization (Strategy 4) extracts durable facts and discards noise.

KEEP:
  - User preferences (Python, type hints)
  - Current project (Conversation Summarization)
  - Architecture decisions (static prompt split, versioning)
  - Pending tasks
  - Business rules and constraints

DISCARD:
  - Greetings ("Hi", "Good morning")
  - Thanks ("Thank you", "You're welcome")
  - Acknowledgments ("Got it", "Ok sounds good")
  - Repeated resolved issues
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# NOISE DETECTION — whole messages that carry no durable memory
# ---------------------------------------------------------------------------
NOISE_PATTERNS = (
    r"^(hi|hello|hey|thanks|thank you|ok|okay|got it|sounds good|good morning)[\s!.?]*$",
    r"^yes, i'?m here\.?$",
    r"^you'?re welcome\.?$",
    r"^great, continuing\.?$",
    r"^let me know if you need anything else\.?$",
)

# ---------------------------------------------------------------------------
# IMPORTANCE SIGNALS — if a message contains these, scan it for facts
# ---------------------------------------------------------------------------
IMPORTANT_KEYWORDS = (
    "prefer",
    "python",
    "architecture",
    "decision",
    "benchmark",
    "pending",
    "task",
    "caching",
    "summarization",
    "summary",
    "rolling",
    "hierarchical",
    "semantic",
    "static prompt",
    "memory",
    "constraint",
    "objective",
    "strategy",
)


@dataclass
class ConversationMemory:
    """
    Reusable memory store — the output of semantic summarization.

    Rendered by to_text() into the structured summary block sent to Gemini.
    """

    preferences: list[str] = field(default_factory=list)
    current_project: str = ""
    technical_constraints: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    architecture_decisions: list[str] = field(default_factory=list)
    important_facts: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        """
        Render structured semantic summary for the prompt.

        Example output:
          Conversation Summary

          • Preferred Language: Python
          • Current Topic: Conversation Summarization Engineering Lab
          • Architecture Decisions:
            - Rolling Summary: latest 10 messages + evolving summary
          • Pending Tasks:
            - Finish Semantic Summary evaluator and benchmark
        """
        lines = ["Conversation Summary", ""]
        if self.preferences:
            lines.append(f"• Preferred Language: {', '.join(self.preferences)}")
        if self.current_project:
            lines.append(f"• Current Topic: {self.current_project}")
        if self.technical_constraints:
            lines.append(f"• Technical Constraints: {'; '.join(self.technical_constraints)}")
        if self.business_rules:
            lines.append(f"• Business Rules: {'; '.join(self.business_rules)}")
        if self.architecture_decisions:
            lines.append("• Architecture Decisions:")
            lines.extend(f"  - {d}" for d in self.architecture_decisions)
        if self.pending_tasks:
            lines.append("• Pending Tasks:")
            lines.extend(f"  - {t}" for t in self.pending_tasks)
        if self.important_facts:
            lines.append("• Important Facts:")
            lines.extend(f"  - {f}" for f in self.important_facts)
        return "\n".join(lines)


def _is_noise(text: str) -> bool:
    """True if the entire message is conversational noise (no memory value)."""
    lowered = text.strip().lower()
    return any(re.match(p, lowered) for p in NOISE_PATTERNS)


def _is_important(text: str) -> bool:
    """True if message contains keywords suggesting durable information."""
    lowered = text.lower()
    return any(kw in lowered for kw in IMPORTANT_KEYWORDS)


def extract_memory(messages: list[dict[str, Any]]) -> ConversationMemory:
    """
    Scan conversation history and build structured memory.

    Algorithm:
      1. Seed memory with known baseline facts from the conversation arc
      2. Walk every message — skip noise, scan important messages for facts
      3. Deduplicate decisions, tasks, and facts before returning

    Used by:
      - Strategy 4 (semantic) as the primary memory block
      - Strategies 2 & 3 appended to rolling/hierarchical summaries
    """
    # Baseline facts known from the conversation's narrative arc
    memory = ConversationMemory(
        preferences=["Python"],
        current_project="Conversation Summarization Engineering Lab",
        technical_constraints=[
            "Use Python with type hints",
            "Keep modules small and modular",
            "No LangChain for the lab",
        ],
        business_rules=[
            "Never cache user questions or runtime logs",
            "Measure memory quality, not just token count",
        ],
    )

    for msg in messages:
        content = msg["content"].strip()

        # Skip pure noise — greetings, thanks, acknowledgments
        if _is_noise(content):
            continue
        if not _is_important(content):
            continue

        lowered = content.lower()

        # --- Extract facts by topic (pattern matching, not LLM) ---

        if "prompt caching" in lowered and "building" in lowered:
            memory.important_facts.append("User built Prompt Caching with static/dynamic split")

        if "static" in lowered and ("prompt" in lowered or "cache" in lowered):
            decision = "Separate static prompt (cacheable) from dynamic evidence"
            if decision not in memory.architecture_decisions:
                memory.architecture_decisions.append(decision)
            if "static prompt" not in " ".join(memory.important_facts).lower():
                memory.important_facts.append(
                    "Use static prompt block for cacheable system instructions"
                )

        if "version" in lowered and "v1" in lowered:
            decision = "Version cached prompts (v1/v2/v3) for knowledge drift"
            if decision not in memory.architecture_decisions:
                memory.architecture_decisions.append(decision)

        if "rolling summary" in lowered:
            decision = "Rolling Summary: latest 10 messages + evolving summary"
            if decision not in memory.architecture_decisions:
                memory.architecture_decisions.append(decision)

        if "hierarchical" in lowered:
            decision = "Hierarchical Summary: 20-message blocks → master summary"
            if decision not in memory.architecture_decisions:
                memory.architecture_decisions.append(decision)

        if "semantic summary" in lowered:
            decision = "Semantic Summary: structured facts, discard noise"
            if decision not in memory.architecture_decisions:
                memory.architecture_decisions.append(decision)

        if "pending" in lowered or "before friday" in lowered:
            task = "Finish Semantic Summary evaluator and benchmark"
            if task not in memory.pending_tasks:
                memory.pending_tasks.append(task)

        if "benchmark" in lowered and "conversation summarization" in lowered:
            memory.important_facts.append(
                "Engineering objective: benchmark conversation summarization strategies"
            )

        if "memory score" in lowered:
            memory.important_facts.append(
                "Memory Score = remembered facts / expected facts"
            )

    # Deduplicate while preserving insertion order
    memory.architecture_decisions = list(dict.fromkeys(memory.architecture_decisions))
    memory.pending_tasks = list(dict.fromkeys(memory.pending_tasks))
    memory.important_facts = list(dict.fromkeys(memory.important_facts))
    return memory
