"""
Chunking strategies for Series 2.3.

Splits documents into retrievable pieces. Token sizes use the same ~4 chars/token
estimate as common/token_usage.py so --dry-run math stays consistent.

Strategies:
  small    — 200 tokens, 0 overlap   (precision, may lose context)
  medium   — 500 tokens, 50 overlap  (balanced default)
  large    — 1000 tokens, 100 overlap (more context, more cost)
  semantic — split on # headings     (structure-aware)
"""

from __future__ import annotations

import re
from typing import Any

# Chars per token — matches common.token_usage.estimate_tokens
CHARS_PER_TOKEN = 4

STRATEGIES: dict[str, dict[str, Any]] = {
    "small": {
        "name": "SMALL CHUNKS",
        "chunk_size": 200,
        "overlap": 0,
        "mode": "fixed",
    },
    "medium": {
        "name": "MEDIUM CHUNKS",
        "chunk_size": 500,
        "overlap": 50,
        "mode": "fixed",
    },
    "large": {
        "name": "LARGE CHUNKS",
        "chunk_size": 1000,
        "overlap": 100,
        "mode": "fixed",
    },
    "semantic": {
        "name": "SEMANTIC CHUNKS",
        "mode": "semantic",
    },
}

HEADING_PATTERN = re.compile(r"^#{1,3}\s+.+", re.MULTILINE)


def _tokens_to_chars(tokens: int) -> int:
    return max(1, tokens * CHARS_PER_TOKEN)


def chunk_fixed(
    text: str,
    document_name: str,
    *,
    chunk_size: int,
    overlap: int = 0,
) -> list[dict[str, Any]]:
    """
    Split text into fixed-size token windows with optional overlap.

    Overlap reduces boundary loss: the end of chunk N overlaps the start of chunk N+1.
    """
    chunk_chars = _tokens_to_chars(chunk_size)
    overlap_chars = _tokens_to_chars(overlap)
    step = max(1, chunk_chars - overlap_chars)

    chunks: list[dict[str, Any]] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_chars, len(text))
        piece = text[start:end].strip()
        if piece:
            index += 1
            start_token = start // CHARS_PER_TOKEN
            end_token = end // CHARS_PER_TOKEN
            chunks.append(
                {
                    "chunk_id": f"{document_name}_chunk_{index:03d}",
                    "document_name": document_name,
                    "text": piece,
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "start_token": start_token,
                    "end_token": end_token,
                }
            )
        if end >= len(text):
            break
        start += step

    return chunks


def chunk_semantic(text: str, document_name: str) -> list[dict[str, Any]]:
    """
    Split on markdown-style headings (# Title).

    Each heading section becomes one chunk — aligned with how docs are structured
    and how users often ask section-level questions.
    """
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return chunk_fixed(text, document_name, chunk_size=500, overlap=0)

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        title = match.group(0).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        sections.append((title, body))

    chunks: list[dict[str, Any]] = []
    for index, (title, body) in enumerate(sections, start=1):
        piece = f"{title}\n\n{body}".strip()
        if not piece:
            continue
        token_est = len(piece) // CHARS_PER_TOKEN
        chunks.append(
            {
                "chunk_id": f"{document_name}_section_{index:03d}",
                "document_name": document_name,
                "text": piece,
                "chunk_size": token_est,
                "overlap": 0,
                "start_token": 0,
                "end_token": token_est,
                "mode": "semantic",
            }
        )
    return chunks


def chunk_document(
    text: str,
    document_name: str,
    strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply one strategy to a single document."""
    if strategy.get("mode") == "semantic":
        return chunk_semantic(text, document_name)

    return chunk_fixed(
        text,
        document_name,
        chunk_size=strategy["chunk_size"],
        overlap=strategy.get("overlap", 0),
    )


def chunk_corpus(documents: dict[str, str], strategy_key: str) -> list[dict[str, Any]]:
    """
    Chunk all documents with one strategy.

    documents: {filename_stem: raw_text}
    Returns flat list of chunk dicts ready for the retriever.
    """
    strategy = STRATEGIES[strategy_key]
    all_chunks: list[dict[str, Any]] = []
    for name, text in documents.items():
        all_chunks.extend(chunk_document(text, name, strategy))
    return all_chunks
