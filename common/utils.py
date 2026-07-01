# HDFS log parsing and question validation (LogHub format)

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# HDFS block IDs look like blk_1073741825 or blk_-8775602795571523802
BLOCK_ID_PATTERN = re.compile(r"blk_[-]?\d+")

# LogHub HDFS line format:
# 081109 203615 148 INFO dfs.DataNode$PacketResponder: message...
HDFS_LINE_PATTERN = re.compile(
    r"^(?P<date>\d+)\s+(?P<time>\d+)\s+(?P<pid>\d+)\s+"
    r"(?P<severity>\w+)\s+(?P<component>[^:]+):\s*(?P<message>.*)$"
)


def extract_block_id(text: str) -> str | None:
    match = BLOCK_ID_PATTERN.search(text)
    return match.group(0) if match else None


def load_hdfs_logs(path: Path | str) -> pd.DataFrame:
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
                # Fallback for lines that don't match the standard pattern
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
    # If block ID is present, scope is clear enough to retrieve logs
    if extract_block_id(question):
        return False
    q = question.strip().lower()
    vague = ("investigate", "issue", "problem", "help", "wrong", "broken")
    return any(word in q for word in vague)
