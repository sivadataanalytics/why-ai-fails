"""
Benchmark questions for Series 2.3 RAG chunking lab.

Each question includes expected_terms used to compute Hit Score:
  Hit Score = matched expected terms / total expected terms

These terms should appear in well-retrieved chunks for the question.
"""

from __future__ import annotations

QUESTIONS = [
    {
        "id": "q1",
        "question": "How is Prompt Caching different from Context Pruning?",
        "expected_terms": [
            "Prompt Caching",
            "Context Pruning",
            "stable knowledge",
            "unnecessary context",
        ],
    },
    {
        "id": "q2",
        "question": "Why does chunk size affect RAG cost?",
        "expected_terms": [
            "chunk size",
            "prompt tokens",
            "latency",
            "cost",
        ],
    },
    {
        "id": "q3",
        "question": "What is Knowledge Drift in prompt caches?",
        "expected_terms": [
            "Knowledge Drift",
            "deprecated APIs",
            "cached prompt",
            "refinement",
        ],
    },
]

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS}
