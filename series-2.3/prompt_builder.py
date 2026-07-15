"""
RAG prompt builder for Series 2.3.
"""

from __future__ import annotations

from typing import Any


def build_rag_prompt(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    """
    Build the prompt sent to Gemini (or estimated in --dry-run).

    Retrieved chunks are labeled with chunk_id and document_name for traceability.
    """
    if retrieved_chunks:
        context_blocks = []
        for chunk in retrieved_chunks:
            header = f"[{chunk['chunk_id']}] ({chunk['document_name']})"
            context_blocks.append(f"{header}\n{chunk['text']}")
        context = "\n\n---\n\n".join(context_blocks)
    else:
        context = "(no chunks retrieved)"

    return f"""You are an AI engineering assistant.

Answer the user question using only the retrieved context.

User Question:
{question}

Retrieved Context:
{context}

Provide:
- Direct answer
- Supporting evidence
- Engineering takeaway
"""
