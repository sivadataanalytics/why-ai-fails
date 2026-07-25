"""
Memory retrieval strategies for Series 2.6.

Pipeline:
  User Request → Intent Detection → Memory Search → Ranking → Top-K → Prompt

Strategies:
  keyword  — exact term overlap via inverted index (fast, simple)
  semantic — TF-IDF cosine similarity (finds related concepts)
  hybrid   — keyword candidates + semantic + metadata boost (enterprise baseline)
  rerank   — hybrid top-20 → full ranking formula → top-K
"""

from __future__ import annotations

import re
from typing import Any

from memory_store import MemoryStore, _tokenize
from ranking import rerank, select_top_k, select_top_k_diverse_values

WORD_PATTERN = re.compile(r"[a-z0-9]+")

# Map intent terms to canonical memory values for explicit boosting
INTENT_VALUE_BOOST: dict[str, str] = {
    "python": "Python",
    "fastapi": "FastAPI",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "secure": "Secure Coding",
    "observability": "AI Observability",
    "readable": "Readable Python",
}

STRATEGIES = ("keyword", "semantic", "hybrid", "rerank")

STRATEGY_NAMES = {
    "keyword": "KEYWORD SEARCH",
    "semantic": "SEMANTIC SEARCH",
    "hybrid": "HYBRID",
    "rerank": "HYBRID + RE-RANKING",
}

# Candidate pool sizes before final top-K
KEYWORD_CANDIDATE_POOL = 200
SEMANTIC_SAMPLE_SIZE = 5000
HYBRID_CANDIDATE_POOL = 300
RERANK_POOL = 20


def _dedupe_best_by_value(
    scored: list[tuple[float, dict[str, Any]]],
) -> list[tuple[float, dict[str, Any]]]:
    """Keep highest-scoring memory per canonical value before re-ranking."""
    best: dict[str, tuple[float, dict[str, Any]]] = {}
    for score, mem in scored:
        value = mem["value"]
        if value not in best or score > best[value][0]:
            best[value] = (score, mem)
    merged = list(best.values())
    merged.sort(key=lambda x: x[0], reverse=True)
    return merged


def detect_intent(query: str, extra_keywords: list[str] | None = None) -> set[str]:
    """Extract intent terms from user query."""
    terms = set(_tokenize(query))
    if extra_keywords:
        terms |= {k.lower() for k in extra_keywords}
    return terms


def _memory_text(mem: dict[str, Any]) -> str:
    return f"{mem['text']} {mem['value']} {mem['category']} {' '.join(mem['tags'])}"


def _boost_intent_memories(
    store: MemoryStore,
    intents: set[str],
) -> list[tuple[float, dict[str, Any]]]:
    """
    Ensure canonical memories for detected intents are in the candidate pool.

    Prevents keyword search from missing Python when FastAPI duplicates dominate scores.
    """
    boosted: list[tuple[float, dict[str, Any]]] = []
    for term, canonical_value in INTENT_VALUE_BOOST.items():
        if term not in intents:
            continue
        best_mem: dict[str, Any] | None = None
        best_rank = -1.0
        for mem in store.active_memories():
            if mem["value"] != canonical_value:
                continue
            rank = mem["confidence"] + mem["recency"] + mem["business_priority"]
            if rank > best_rank:
                best_rank = rank
                best_mem = mem
        if best_mem:
            boosted.append((1000.0 + best_rank, best_mem))
    return boosted


def keyword_search(
    store: MemoryStore,
    query: str,
    *,
    intent_keywords: list[str] | None = None,
    pool_size: int = KEYWORD_CANDIDATE_POOL,
) -> list[tuple[float, dict[str, Any]]]:
    """
    Strategy 1 — Keyword search via inverted index.

    Scores by count of query terms found in memory. Fast, but requires exact wording overlap.
    """
    intents = detect_intent(query, intent_keywords)
    candidate_indices: set[int] = set()
    for term in intents:
        candidate_indices |= store.inverted_index.get(term, set())

    if not candidate_indices:
        # Fallback: scan active subset by partial match (limited)
        for i, mem in enumerate(store.memories[:pool_size * 2]):
            if not mem.get("obsolete"):
                candidate_indices.add(i)

    scored: list[tuple[float, dict[str, Any]]] = []
    for idx in candidate_indices:
        mem = store.memories[idx]
        if mem.get("obsolete"):
            continue
        text_terms = set(_tokenize(_memory_text(mem)))
        tag_set = set(mem.get("tags", []))
        overlap = len(intents & text_terms)
        tag_overlap = len(intents & tag_set)
        # Boost each intent term matched in value directly
        value_lower = mem["value"].lower()
        value_hits = sum(1 for t in intents if t in value_lower or t in " ".join(tag_set))
        boost_value = sum(
            8.0 for term, val in INTENT_VALUE_BOOST.items()
            if term in intents and mem["value"] == val
        )
        score = (
            overlap * 2.0
            + tag_overlap * 4.0
            + value_hits * 5.0
            + boost_value
            + mem["confidence"] * 0.5
            + mem["business_priority"] * 0.3
        )
        if score > 0:
            scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:pool_size]


def semantic_search(
    store: MemoryStore,
    query: str,
    *,
    intent_keywords: list[str] | None = None,
    sample_size: int = SEMANTIC_SAMPLE_SIZE,
) -> list[tuple[float, dict[str, Any]]]:
    """
    Strategy 2 — Semantic search via TF-IDF cosine similarity.

    Finds related concepts even when exact keywords differ.
    Samples active memories for performance on 100k store.
    """
    query_text = query + " " + " ".join(intent_keywords or [])
    query_vec = store.tfidf_vector(query_text)

    scored: list[tuple[float, dict[str, Any]]] = []
    active = store.active_memories()
    step = max(1, len(active) // sample_size)

    for i in range(0, len(active), step):
        mem = active[i]
        doc_vec = store.tfidf_vector(_memory_text(mem))
        sim = store.cosine_similarity(query_vec, doc_vec)
        if sim > 0.01:
            scored.append((sim, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:KEYWORD_CANDIDATE_POOL]


def hybrid_search(
    store: MemoryStore,
    query: str,
    *,
    intent_keywords: list[str] | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    """
    Strategy 3 — Hybrid: keyword candidates + semantic similarity + metadata.

    Enterprise baseline — combines speed of keyword index with semantic scoring.
    """
    kw_scored = keyword_search(store, query, intent_keywords=intent_keywords, pool_size=HYBRID_CANDIDATE_POOL)
    query_text = query + " " + " ".join(intent_keywords or [])
    query_vec = store.tfidf_vector(query_text)
    intents = detect_intent(query, intent_keywords)

    combined: dict[str, tuple[float, dict[str, Any]]] = {}
    max_kw = max((s for s, _ in kw_scored), default=1.0)

    for kw_score, mem in kw_scored:
        doc_vec = store.tfidf_vector(_memory_text(mem))
        semantic_sim = store.cosine_similarity(query_vec, doc_vec)
        tag_boost = len(intents & set(mem.get("tags", []))) * 0.2
        category_boost = 0.15 if any(t in mem["category"].lower() for t in intents) else 0
        norm_kw = kw_score / max(max_kw, 1.0)
        hybrid_score = (
            0.30 * norm_kw
            + 0.45 * semantic_sim
            + 0.10 * mem["confidence"]
            + 0.10 * mem["recency"]
            + 0.05 * mem["business_priority"]
            + tag_boost
            + category_boost
        )
        combined[mem["memory_id"]] = (hybrid_score, mem)

    # Add top semantic-only hits + intent coverage boost
    for sem_score, mem in semantic_search(store, query, intent_keywords=intent_keywords)[:50]:
        if mem["memory_id"] not in combined:
            combined[mem["memory_id"]] = (sem_score * 0.7, mem)

    for boost_score, mem in _boost_intent_memories(store, intents):
        normalized = boost_score / 100.0
        existing = combined.get(mem["memory_id"])
        if existing is None or normalized > existing[0]:
            combined[mem["memory_id"]] = (normalized, mem)

    result = list(combined.values())
    result.sort(key=lambda x: x[0], reverse=True)
    return result[:HYBRID_CANDIDATE_POOL]


def retrieve(
    store: MemoryStore,
    query: str,
    strategy: str,
    *,
    top_k: int = 5,
    intent_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run one retrieval strategy and return top-K memories.
    """
    if strategy == "keyword":
        scored = keyword_search(store, query, intent_keywords=intent_keywords)
        return select_top_k(scored, top_k)

    if strategy == "semantic":
        scored = semantic_search(store, query, intent_keywords=intent_keywords)
        return select_top_k(scored, top_k)

    if strategy == "hybrid":
        scored = hybrid_search(store, query, intent_keywords=intent_keywords)
        return select_top_k(scored, top_k)

    if strategy == "rerank":
        scored = hybrid_search(store, query, intent_keywords=intent_keywords)
        intents = detect_intent(query, intent_keywords)
        deduped = _dedupe_best_by_value(scored)
        pool_map: dict[str, tuple[float, dict[str, Any]]] = {
            mem["memory_id"]: (score, mem) for score, mem in deduped[:RERANK_POOL]
        }
        for boost_score, mem in _boost_intent_memories(store, intents):
            pool_map[mem["memory_id"]] = (boost_score / 100.0, mem)

        query_vec = store.tfidf_vector(query + " " + " ".join(intent_keywords or []))
        candidates: list[tuple[float, dict[str, Any]]] = []
        for _, mem in pool_map.values():
            sim = store.cosine_similarity(query_vec, store.tfidf_vector(_memory_text(mem)))
            intent_bonus = sum(
                0.25 for term, val in INTENT_VALUE_BOOST.items()
                if term in intents and mem["value"] == val
            )
            candidates.append((sim + intent_bonus, mem))

        ranked = rerank(candidates, top_k=top_k * 3)
        return select_top_k_diverse_values(
            [(m.get("rank_score", 0), m) for m in ranked],
            top_k,
        )

    raise ValueError(f"Unknown strategy: {strategy}")
