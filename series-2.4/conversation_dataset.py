"""
Synthetic enterprise AI coding assistant conversation (~178 messages).

WHY SYNTHETIC?
--------------
Real chat logs contain PII and are hard to share in a lab repo.
This generator creates enough conversational noise to prove why summarization
matters — greetings, small talk, repeated explanations, architecture reviews.

CONVERSATION ARC
----------------
  Phase 1 — Onboarding: Python preference, type hints, modular code
  Phase 2 — Prompt Caching project: static/dynamic split, versioning, drift
  Phase 3 — RAG chunking side note (links to Series 2.3)
  Phase 4 — Conversation Summarization lab: four strategies, benchmark, pending tasks
  Loops   — Small talk + topic loops pad to ~178 messages (realistic noise)

USED BY
-------
  conversation_loader.py → app.py
  EXPECTED_MEMORY_FACTS  → evaluator.py (Memory Score)
  BENCHMARK_QUESTIONS    → app.py (--question-id)
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# EXPECTED MEMORY FACTS — summarization must preserve these (evaluator.py)
# Memory Score = how many of these appear in memory + latest messages
# ---------------------------------------------------------------------------
EXPECTED_MEMORY_FACTS = [
    "Python",
    "Prompt Caching",
    "Conversation Summarization",
    "benchmark",
    "Rolling Summary",
    "Hierarchical Summary",
    "Semantic Summary",
    "static prompt",
    "pending",
]

# ---------------------------------------------------------------------------
# BENCHMARK QUESTIONS — test memory quality with realistic assistant queries
# Each question has expected_facts for per-question evaluation (optional)
# ---------------------------------------------------------------------------
BENCHMARK_QUESTIONS = [
    {
        "id": "q1",
        "question": "What programming language does the user prefer?",
        "expected_facts": ["Python"],
    },
    {
        "id": "q2",
        "question": "What project is the user currently working on?",
        "expected_facts": ["Conversation Summarization", "Prompt Caching"],
    },
    {
        "id": "q3",
        "question": "What architectural decisions have already been made?",
        "expected_facts": ["static prompt", "Rolling Summary", "Hierarchical Summary"],
    },
    {
        "id": "q4",
        "question": "What task is still pending?",
        "expected_facts": ["Semantic Summary", "benchmark", "pending"],
    },
    {
        "id": "q5",
        "question": "Summarize the current engineering objective.",
        "expected_facts": ["Conversation Summarization", "benchmark", "memory"],
    },
]

QUESTIONS_BY_ID = {q["id"]: q for q in BENCHMARK_QUESTIONS}


def _pair(user: str, assistant: str) -> list[dict[str, str]]:
    """Helper — one user turn + one assistant reply."""
    return [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]


def generate_conversation() -> list[dict[str, Any]]:
    """
    Build an ordered conversation with 150–200 messages.

    Messages are generated programmatically (not loaded from file) so the lab
    is self-contained and reproducible.
    """
    messages: list[dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # PHASE 1 — Onboarding and user preferences
    # Key fact embedded: "I prefer Python"
    # -----------------------------------------------------------------------
    messages.extend(
        _pair(
            "Hi, I'm building an enterprise AI assistant for our platform team.",
            "Hello! Happy to help. What stack and goals should we keep in mind?",
        )
    )
    messages.extend(
        _pair(
            "I prefer Python for all backend services and benchmarks.",
            "Great. I'll use Python for examples and generated code.",
        )
    )
    messages.extend(
        _pair(
            "Thanks! Also use type hints and keep modules small.",
            "Understood — typed, modular Python it is.",
        )
    )

    # -----------------------------------------------------------------------
    # PHASE 2 — Prompt Caching project (links to Series 2.2)
    # Key facts: static prompt, versioning, knowledge drift
    # -----------------------------------------------------------------------
    messages.extend(
        _pair(
            "I'm building Prompt Caching for our AI platform.",
            "Let's design it. We'll split static system prompts from dynamic user evidence.",
        )
    )
    messages.extend(
        _pair(
            "Static prompt holds role, rules, schema — keep it separate from dynamic evidence.",
            "Architecture decision: static prompt is cacheable; dynamic user content is never cached.",
        )
    )
    messages.extend(
        _pair(
            "Architecture decision: version cached prompts as v1, v2, v3 for knowledge drift.",
            "Good call. Versioning helps detect stale cached instructions.",
        )
    )

    # Reusable small talk — pads message count with low-value noise
    small_talk = [
        ("Good morning!", "Good morning! Ready when you are."),
        ("Quick question — are you there?", "Yes, I'm here."),
        ("Thank you!", "You're welcome."),
        ("Got it.", "Let me know if you need anything else."),
        ("Ok sounds good.", "Great, continuing."),
    ]

    # Prompt caching depth topics — repeated to simulate long thread
    caching_topics = [
        (
            "How should we bill cache hits vs misses?",
            "Miss pays full static tokens; hit pays dynamic plus discounted cached static tokens.",
        ),
        (
            "Should completion tokens dominate total cost?",
            "Often yes — still measure input cost reduction separately for caching ROI.",
        ),
        (
            "Can we warm the cache on deploy?",
            "Yes — first request is a miss; subsequent requests hit the warm cache.",
        ),
        (
            "What about Knowledge Drift?",
            "Monitor deprecated APIs in cached prompts; schedule refinement and invalidation.",
        ),
    ]

    # Loop until ~90 messages — mix noise + substance
    idx = 0
    while len(messages) < 90:
        u, a = small_talk[idx % len(small_talk)]
        messages.extend(_pair(u, a))
        u2, a2 = caching_topics[idx % len(caching_topics)]
        messages.extend(_pair(u2, a2))
        idx += 1

    # -----------------------------------------------------------------------
    # PHASE 3 — RAG chunking side discussion (links to Series 2.3)
    # -----------------------------------------------------------------------
    messages.extend(
        _pair(
            "Side note — we also benchmarked RAG chunking last sprint.",
            "Chunk size affects retrieval quality, prompt tokens, and latency together.",
        )
    )
    messages.extend(
        _pair(
            "Medium chunks were the best balance for our docs corpus.",
            "Benchmark beat guessing — small chunks missed cross-section context sometimes.",
        )
    )

    # -----------------------------------------------------------------------
    # PHASE 4 — Pivot to Conversation Summarization (this lab)
    # Key facts: four strategies, memory score, pending tasks
    # -----------------------------------------------------------------------
    messages.extend(
        _pair(
            "New focus: Conversation Summarization engineering lab for Series 2.4.",
            "Summarization is memory management — not just token optimization.",
        )
    )
    messages.extend(
        _pair(
            "We need four strategies: full, rolling, hierarchical, and semantic.",
            "Full sends everything; the others preserve memory with less noise.",
        )
    )
    messages.extend(
        _pair(
            "Rolling Summary should keep the latest 10 messages plus an evolving summary.",
            "Older turns compress into summary; recent context stays verbatim.",
        )
    )
    messages.extend(
        _pair(
            "Hierarchical Summary: every 20 messages become a block summary, then a master summary.",
            "That scales to very long threads without one giant rolling summary.",
        )
    )
    messages.extend(
        _pair(
            "Semantic Summary should keep preferences, decisions, tasks — drop greetings.",
            "Extract structured memory: language, project, constraints, pending tasks.",
        )
    )

    summarization_topics = [
        (
            "Please generate benchmark code for conversation summarization.",
            "Certainly — we'll compare prompt tokens, latency, cost, and memory score.",
        ),
        (
            "Pending task: finish Semantic Summary evaluator before Friday.",
            "Noted — Semantic Summary benchmark and memory score validation remain pending.",
        ),
        (
            "Repeat: user prefers Python and modular files.",
            "Confirmed — Python, type hints, small modules.",
        ),
        (
            "What's the engineering objective?",
            "Build a benchmark proving summarization preserves memory at lower token cost.",
        ),
        (
            "Should Gemini see the full 175-message history?",
            "No — only conversation memory plus latest messages after summarization.",
        ),
        (
            "How do we score memory quality?",
            "Memory Score = remembered facts / expected facts in the compressed context.",
        ),
    ]

    # Loop until 175+ messages — more noise + summarization topics
    idx = 0
    while len(messages) < 175:
        u, a = small_talk[idx % len(small_talk)]
        messages.extend(_pair(u, a))
        u2, a2 = summarization_topics[idx % len(summarization_topics)]
        messages.extend(_pair(u2, a2))
        idx += 1

    # Tag each message with a 1-based index for traceability
    for i, msg in enumerate(messages, start=1):
        msg["index"] = i

    return messages
