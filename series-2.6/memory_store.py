"""
Memory store with inverted index for Series 2.6.

Loads 100k records and builds keyword index + IDF weights for semantic scoring.
"""

from __future__ import annotations

import math
import re
from typing import Any

from memories import generate_memories

WORD_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(text.lower())


class MemoryStore:
    """
    In-memory store for 100k records.

    Builds:
      - inverted index: term → set of memory indices
      - idf weights for TF-IDF semantic similarity
    """

    def __init__(self, memories: list[dict[str, Any]] | None = None) -> None:
        self.memories: list[dict[str, Any]] = memories or []
        self.inverted_index: dict[str, set[int]] = {}
        self.idf: dict[str, float] = {}
        if self.memories:
            self._build_index()

    @classmethod
    def load(cls, count: int = 100_000) -> MemoryStore:
        """Generate and index memory dataset."""
        return cls(generate_memories(count))

    def _build_index(self) -> None:
        """Build inverted index and IDF from all memory text."""
        n = len(self.memories)
        doc_freq: dict[str, int] = {}

        for i, mem in enumerate(self.memories):
            text = f"{mem['text']} {mem['value']} {mem['category']} {' '.join(mem['tags'])}"
            terms = set(_tokenize(text))
            for term in terms:
                self.inverted_index.setdefault(term, set()).add(i)
                doc_freq[term] = doc_freq.get(term, 0) + 1

        for term, df in doc_freq.items():
            self.idf[term] = math.log((n + 1) / (df + 1)) + 1.0

    def size(self) -> int:
        return len(self.memories)

    def active_memories(self) -> list[dict[str, Any]]:
        """Non-obsolete memories only."""
        return [m for m in self.memories if not m.get("obsolete")]

    def get_by_indices(self, indices: set[int]) -> list[dict[str, Any]]:
        return [self.memories[i] for i in sorted(indices)]

    def tfidf_vector(self, text: str) -> dict[str, float]:
        """Compute TF-IDF vector for a text string."""
        terms = _tokenize(text)
        if not terms:
            return {}
        tf: dict[str, float] = {}
        for t in terms:
            tf[t] = tf.get(t, 0) + 1.0
        for t in tf:
            tf[t] /= len(terms)
            tf[t] *= self.idf.get(t, 1.0)
        return tf

    @staticmethod
    def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
        """Cosine similarity between two sparse TF-IDF vectors."""
        if not vec_a or not vec_b:
            return 0.0
        dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in set(vec_a) | set(vec_b))
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
