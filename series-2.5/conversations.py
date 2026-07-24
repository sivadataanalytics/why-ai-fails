"""
Synthetic conversation dataset for Series 2.5 (~500 conversations).

Same user appears across all conversations. Topics rotate through:
  Python, FastAPI, Observability, Prompt Caching, RAG, Conversation Summarization,
  Security, Unit Testing, PostgreSQL, Kubernetes

Intentionally includes:
  - duplicate preferences (same fact stated many times)
  - changing preferences (PyCharm → VS Code around conversation 350)
  - temporary information (short TTL, expires during compression)
  - obsolete information (old project names superseded by updates)
"""

from __future__ import annotations

from typing import Any

CONVERSATION_COUNT = 500
USER_ID = "user_platform_eng_001"

TOPICS = [
    "Python",
    "FastAPI",
    "Observability",
    "Prompt Caching",
    "RAG",
    "Conversation Summarization",
    "Security",
    "Unit Testing",
    "PostgreSQL",
    "Kubernetes",
]

# Used by evaluator.py for Retrieval Accuracy
EXPECTED_MEMORIES = [
    "Python",
    "FastAPI",
    "Secure Coding",
    "PostgreSQL",
    "Readable Python",
]

BENCHMARK_QUESTIONS = [
    {
        "id": "q1",
        "question": "Generate a secure FastAPI REST API.",
        "expected_memories": ["FastAPI", "Secure Coding", "Python"],
        "intent_keywords": ["fastapi", "secure", "rest", "api"],
    },
    {
        "id": "q2",
        "question": "Generate Python code.",
        "expected_memories": ["Python", "Readable Python"],
        "intent_keywords": ["python", "code"],
    },
    {
        "id": "q3",
        "question": "What framework does the user prefer?",
        "expected_memories": ["FastAPI"],
        "intent_keywords": ["framework", "prefer"],
    },
    {
        "id": "q4",
        "question": "Which database should be used?",
        "expected_memories": ["PostgreSQL"],
        "intent_keywords": ["database", "postgres"],
    },
    {
        "id": "q5",
        "question": "Generate code following organization standards.",
        "expected_memories": ["Secure Coding", "Readable Python"],
        "intent_keywords": ["organization", "standards", "secure"],
    },
]

QUESTIONS_BY_ID = {q["id"]: q for q in BENCHMARK_QUESTIONS}


def _pair(user: str, assistant: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]


def _topic_conversation(conv_id: int, topic: str) -> dict[str, Any]:
    """Generate one conversation focused on a topic — yields extractable memories."""
    messages: list[dict[str, str]] = []

    # Core preferences repeated across many conversations (duplicate memories)
    if conv_id % 3 == 0:
        messages.extend(
            _pair(
                "Reminder: I prefer Python with readable, well-typed code.",
                "Noted — Python with readable style and type hints.",
            )
        )

    if conv_id % 5 == 0:
        messages.extend(
            _pair(
                "I usually develop REST APIs using FastAPI.",
                "I'll default to FastAPI for API examples and scaffolding.",
            )
        )

    if conv_id % 7 == 0:
        messages.extend(
            _pair(
                "Our organization requires secure coding — never store credentials in code.",
                "Understood — secure coding standards apply to all generated code.",
            )
        )

    if conv_id % 11 == 0:
        messages.extend(
            _pair(
                "We standardize on PostgreSQL for persistence layers.",
                "PostgreSQL will be the default database recommendation.",
            )
        )

    # Topic-specific turns
    topic_templates: dict[str, tuple[str, str]] = {
        "Python": (
            "Show me readable Python patterns for service modules.",
            "I'll use clear naming and small functions — readable Python style.",
        ),
        "FastAPI": (
            "Help me scaffold a FastAPI router with Pydantic models.",
            "FastAPI + Pydantic is a solid Python backend stack.",
        ),
        "Observability": (
            "Add observability metrics to our AI Observability platform.",
            "We'll instrument latency, token usage, and error rates.",
        ),
        "Prompt Caching": (
            "Review our Prompt Caching design for static vs dynamic prompts.",
            "Cache static system prompts; never cache runtime evidence.",
        ),
        "RAG": (
            "Tune RAG chunk size for our documentation corpus.",
            "Benchmark chunk strategies — retrieval quality per token matters.",
        ),
        "Conversation Summarization": (
            "Implement conversation summarization for long chat sessions.",
            "Summarize history into durable memory, not a message archive.",
        ),
        "Security": (
            "Audit this module for secure coding violations.",
            "Checking for credential leaks and injection risks per org standards.",
        ),
        "Unit Testing": (
            "Write unit tests for the memory compression engine.",
            "I'll use pytest with readable Python test names.",
        ),
        "PostgreSQL": (
            "Design a PostgreSQL schema for long-term user memory.",
            "PostgreSQL JSONB works well for structured memory profiles.",
        ),
        "Kubernetes": (
            "Deploy the memory service on Kubernetes with health checks.",
            "Kubernetes deployment with liveness probes for the memory API.",
        ),
    }

    u, a = topic_templates.get(topic, topic_templates["Python"])
    messages.extend(_pair(u, a))

    # Changing preference: IDE switches mid-dataset (memory UPDATE, not duplicate)
    if conv_id < 350:
        if conv_id % 23 == 0:
            messages.extend(
                _pair(
                    "My preferred IDE is PyCharm for Python work.",
                    "I'll reference PyCharm-oriented workflows when helpful.",
                )
            )
    else:
        if conv_id % 23 == 0:
            messages.extend(
                _pair(
                    "I switched my preferred IDE to VS Code with Python extensions.",
                    "VS Code is now your preferred IDE — I'll update that preference.",
                )
            )

    # Temporary information — expires during compression (low TTL)
    if conv_id % 41 == 0:
        messages.extend(
            _pair(
                "Temporary: debugging a prod incident tonight only — ignore after 24h.",
                "Marked temporary — this context should not persist long-term.",
            )
        )

    # Obsolete project — superseded by update in later conversations
    if 100 <= conv_id < 200 and conv_id % 17 == 0:
        messages.extend(
            _pair(
                "Current project codename is LegacyBot — focus docs there.",
                "Tracking LegacyBot as the active project.",
            )
        )
    if conv_id >= 200 and conv_id % 17 == 0:
        messages.extend(
            _pair(
                "Project renamed: Long-Term Memory engine replaces LegacyBot.",
                "Updated — Long-Term Memory is the current project focus.",
            )
        )

    # Stack components for consolidation (FastAPI + Pydantic + SQLAlchemy)
    if conv_id % 19 == 0:
        messages.extend(
            _pair(
                "We use Pydantic for validation and SQLAlchemy for ORM layers.",
                "Pydantic and SQLAlchemy are part of your Python backend stack.",
            )
        )

    return {
        "conversation_id": conv_id,
        "user_id": USER_ID,
        "topic": topic,
        "messages": messages,
    }


def generate_conversations(count: int = CONVERSATION_COUNT) -> list[dict[str, Any]]:
    """Build `count` simulated conversations for the same enterprise user."""
    conversations: list[dict[str, Any]] = []
    for i in range(1, count + 1):
        topic = TOPICS[(i - 1) % len(TOPICS)]
        conversations.append(_topic_conversation(i, topic))
    return conversations
