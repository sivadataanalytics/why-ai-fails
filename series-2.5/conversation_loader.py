"""
Load simulated conversations for Series 2.5.
"""

from __future__ import annotations

from typing import Any

from conversations import CONVERSATION_COUNT, generate_conversations


def load_conversations(count: int = CONVERSATION_COUNT) -> list[dict[str, Any]]:
    """Return ordered list of simulated user conversations."""
    return generate_conversations(count)
