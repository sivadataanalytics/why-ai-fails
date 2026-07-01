# Context pruning for HDFS logs — filter, dedupe, summarize before sending to LLM

from __future__ import annotations

from typing import Any

import pandas as pd

from common.utils import extract_block_id


def filter_logs_for_block(logs: pd.DataFrame, block_id: str) -> pd.DataFrame:
    # Keep rows whose message or block_id column matches the target block
    mask = logs["message"].str.contains(block_id, na=False, regex=False)
    if logs["block_id"].notna().any():
        mask = mask | (logs["block_id"] == block_id)
    return logs[mask].copy()


def keep_useful_columns(logs: pd.DataFrame) -> pd.DataFrame:
    # Drop raw line and other noise — only fields needed for investigation
    columns = ["timestamp", "severity", "component", "message", "block_id"]
    existing = [c for c in columns if c in logs.columns]
    return logs[existing].copy()


def deduplicate_messages(logs: pd.DataFrame) -> pd.DataFrame:
    # Same message repeated across nodes still costs tokens if sent twice
    return logs.drop_duplicates(subset=["message"]).reset_index(drop=True)


def limit_relevant_rows(logs: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    # Prefer ERROR/WARN over INFO; cap rows to control prompt size
    if logs.empty:
        return logs
    severity_rank = {"ERROR": 0, "WARN": 1, "WARNING": 1, "INFO": 2, "DEBUG": 3}
    logs = logs.copy()
    logs["_rank"] = logs["severity"].str.upper().map(severity_rank).fillna(9)
    logs = logs.sort_values(["_rank", "timestamp"]).drop(columns="_rank")
    return logs.head(max_rows).reset_index(drop=True)


def summarize_evidence(logs: pd.DataFrame, block_id: str) -> dict[str, Any]:
    # Compact summary replaces thousands of raw log lines in the prompt
    severities = logs["severity"].str.upper()
    error_count = int(severities.isin(["ERROR", "ERR", "FATAL"]).sum())
    warning_count = int(severities.isin(["WARN", "WARNING"]).sum())

    top_messages = logs["message"].head(10).tolist()
    components = sorted(logs["component"].dropna().unique().tolist())

    if logs.empty:
        summary = f"No log lines found for block {block_id}."
    else:
        summary = (
            f"Found {len(logs)} relevant lines for {block_id}. "
            f"Components involved: {', '.join(components) or 'unknown'}. "
            f"Errors={error_count}, warnings={warning_count}."
        )

    return {
        "block_id": block_id,
        "relevant_log_count": len(logs),
        "error_count": error_count,
        "warning_count": warning_count,
        "top_messages": top_messages,
        "summary": summary,
    }


def prune_hdfs_context(logs: pd.DataFrame, user_question: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    # Full pipeline: extract block ID → filter → trim → dedupe → summarize
    block_id = extract_block_id(user_question)
    if not block_id:
        raise ValueError("No block ID in question. Example: blk_-8775602795571523802")

    filtered = filter_logs_for_block(logs, block_id)
    filtered = keep_useful_columns(filtered)
    filtered = deduplicate_messages(filtered)
    filtered = limit_relevant_rows(filtered)
    evidence = summarize_evidence(filtered, block_id)
    return filtered, evidence
