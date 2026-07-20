"""
Load conversation dataset for Series 2.4.

Thin wrapper around conversation_dataset.generate_conversation().
Keeps app.py imports clean — loader vs generator separation.
"""

from __future__ import annotations

from typing import Any

from conversation_dataset import generate_conversation


def load_conversation() -> list[dict[str, Any]]:
    """
    Return ordered conversation messages.

    Each message: {"role": "user"|"assistant", "content": "...", "index": N}
    Total count: ~178 messages (target was 150–200).
    """
    return generate_conversation()
