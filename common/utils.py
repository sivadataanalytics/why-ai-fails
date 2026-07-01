"""
HDFS log parsing and pre-retrieval token guards.

load_hdfs_logs()      — parse raw LogHub file into structured DataFrame
extract_block_id()  — pull block ID from user question (enables scoped filtering)
is_ambiguous_question() — TOKEN GUARD: stop before loading logs if scope is unclear
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# HDFS block IDs: blk_1073741825 or blk_-8775602795571523802
BLOCK_ID_PATTERN = re.compile(r"blk_[-]?\d+")

# LogHub format: 081109 203615 148 INFO dfs.DataNode$PacketResponder: message...
HDFS_LINE_PATTERN = re.compile(
    r"^(?P<date>\d+)\s+(?P<time>\d+)\s+(?P<pid>\d+)\s+"
    r"(?P<severity>\w+)\s+(?P<component>[^:]+):\s*(?P<message>.*)$"
)


def extract_block_id(text: str) -> str | None:
    """Extract block ID from user question — required for scoped log filtering."""
    match = BLOCK_ID_PATTERN.search(text)
    return match.group(0) if match else None


def load_hdfs_logs(path: Path | str) -> pd.DataFrame:
    """
    Parse HDFS log file into structured rows.

    Returns DataFrame with 'raw' column (full line) used by unpruned flow,
    and structured columns used by prune.py for filtering.
    """
    rows: list[dict[str, str]] = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            parsed = HDFS_LINE_PATTERN.match(line)
            if parsed:
                groups = parsed.groupdict()
                message = groups["message"]
                block_id = extract_block_id(message) or extract_block_id(line) or ""
                rows.append(
                    {
                        "timestamp": f"{groups['date']} {groups['time']}",
                        "severity": groups["severity"],
                        "component": groups["component"].strip(),
                        "message": message,
                        "block_id": block_id,
                        "raw": line,
                    }
                )
            else:
                rows.append(
                    {
                        "timestamp": "",
                        "severity": "",
                        "component": "",
                        "message": line,
                        "block_id": extract_block_id(line) or "",
                        "raw": line,
                    }
                )
    return pd.DataFrame(rows)


def is_ambiguous_question(question: str) -> bool:
    """
    TOKEN GUARD — clarify first, retrieve later.

    If the question has no block ID and sounds vague ("investigate the issue"),
    return True so app.py asks clarifying questions instead of loading 2000 log lines.

    Loading logs before scope is known = wasted retrieval + wasted tokens.
    """
    if extract_block_id(question):
        return False
    q = question.strip().lower()
    vague = ("investigate", "issue", "problem", "help", "wrong", "broken")
    return any(word in q for word in vague)
