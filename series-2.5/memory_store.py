"""
Structured long-term memory store for Series 2.5.

Long-term memory is NOT a conversation archive — it is a compressed knowledge base.
"""

from __future__ import annotations

import json
from typing import Any

from common.token_usage import estimate_tokens


class MemoryStore:
    """In-memory store with JSON profile export."""

    def __init__(self, memories: list[dict[str, Any]] | None = None) -> None:
        self.memories: list[dict[str, Any]] = list(memories or [])

    def size(self) -> int:
        """Memory size in estimated tokens (storage cost proxy)."""
        return estimate_tokens(self.to_json())

    def count(self) -> int:
        return len(self.memories)

    def to_json(self) -> str:
        """Export structured JSON profile."""
        profile = self.to_profile()
        return json.dumps(profile, indent=2)

    def to_profile(self) -> dict[str, Any]:
        """
        Build human-readable profile JSON matching the lab spec.

        Example shape:
          user_profile, projects, organization, technical, memories
        """
        profile: dict[str, Any] = {
            "user_profile": {},
            "projects": [],
            "organization": {},
            "technical": [],
            "memory_records": len(self.memories),
        }

        projects: set[str] = set()
        technical: set[str] = set()

        for mem in self.memories:
            cat = mem["category"]
            key = mem["key"]
            val = mem["value"]

            if cat == "User Preferences":
                profile["user_profile"][key] = val
            elif cat == "Project Information" and key == "project":
                projects.add(val)
            elif cat == "Project Information" and key == "topic":
                projects.add(val)
            elif cat == "Organization Standards":
                profile["organization"][key] = val
            elif cat == "Coding Style":
                profile["user_profile"][key] = val
            else:
                technical.add(val)

        profile["projects"] = sorted(projects)
        profile["technical"] = sorted(technical)
        return profile

    def to_context_text(self, memories: list[dict[str, Any]] | None = None) -> str:
        """Render memories as text block for prompt injection."""
        items = memories if memories is not None else self.memories
        lines = ["Long-Term User Memory:", ""]
        for mem in items:
            lines.append(
                f"- [{mem['category']}] {mem['key']}: {mem['value']} "
                f"(confidence={mem['confidence']})"
            )
        return "\n".join(lines)
