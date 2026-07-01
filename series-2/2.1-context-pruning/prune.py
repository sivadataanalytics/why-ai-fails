"""
Context pruning pipeline for HDFS logs.

CORE IDEA — TOKEN PRUNING
-------------------------
Before calling the LLM, shrink the context to only what matters:

  2000 log lines  →  filter by block ID  →  ~2 lines
                  →  drop duplicate messages
                  →  keep ERROR/WARN first
                  →  summarize into counts + top messages
                  →  ~200 tokens in the final prompt

Each function below removes tokens that would otherwise be billed but add
no value to answering the investigation question.

Pipeline order matters — filter first (biggest win), then dedupe, then cap.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from common.utils import extract_block_id


def filter_logs_for_block(logs: pd.DataFrame, block_id: str) -> pd.DataFrame:
    """
    TOKEN PRUNE STEP 1 — Scope filter (largest savings).

    From 2000 lines, keep only rows mentioning the target block ID.
    Typical result: 2000 → 2 lines (~99.9% of log tokens eliminated here).
    """
    mask = logs["message"].str.contains(block_id, na=False, regex=False)
    if logs["block_id"].notna().any():
        mask = mask | (logs["block_id"] == block_id)
    return logs[mask].copy()


def keep_useful_columns(logs: pd.DataFrame) -> pd.DataFrame:
    """
    TOKEN PRUNE STEP 2 — Column filter.

    Drop the 'raw' full log line column and other fields not needed for diagnosis.
    Smaller rows = fewer characters = fewer tokens per remaining line.
    """
    columns = ["timestamp", "severity", "component", "message", "block_id"]
    existing = [c for c in columns if c in logs.columns]
    return logs[existing].copy()


def deduplicate_messages(logs: pd.DataFrame) -> pd.DataFrame:
    """
    TOKEN PRUNE STEP 3 — Deduplication.

    Identical messages on different nodes are still the same information.
    Sending duplicates wastes tokens without adding evidence.
    """
    return logs.drop_duplicates(subset=["message"]).reset_index(drop=True)


def limit_relevant_rows(logs: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    """
    TOKEN PRUNE STEP 4 — Row cap with severity priority.

    If many rows remain, keep ERROR/WARN first (most diagnostic), drop INFO noise.
    Hard cap at max_rows prevents runaway prompt size.
    """
    if logs.empty:
        return logs
    severity_rank = {"ERROR": 0, "WARN": 1, "WARNING": 1, "INFO": 2, "DEBUG": 3}
    logs = logs.copy()
    logs["_rank"] = logs["severity"].str.upper().map(severity_rank).fillna(9)
    logs = logs.sort_values(["_rank", "timestamp"]).drop(columns="_rank")
    return logs.head(max_rows).reset_index(drop=True)


def summarize_evidence(logs: pd.DataFrame, block_id: str) -> dict[str, Any]:
    """
    TOKEN PRUNE STEP 5 — Summarize instead of replaying raw logs.

    Replace N log lines with a compact evidence dict:
      - counts (errors, warnings)
      - top 10 messages only
      - one-line summary

    This is the biggest token win after filtering — summary beats raw dump.
    """
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
    """
    Full context pruning pipeline — run all 5 steps in sequence.

    Input:  full DataFrame (e.g. 2000 rows) + user question with block ID
    Output: pruned DataFrame (few rows) + evidence dict for prompt_builder

    The evidence dict feeds build_pruned_prompt() which produces a ~200-token
    prompt instead of a ~71,000-token raw log dump.
    """
    block_id = extract_block_id(user_question)
    if not block_id:
        raise ValueError("No block ID in question. Example: blk_-8775602795571523802")

    filtered = filter_logs_for_block(logs, block_id)
    filtered = keep_useful_columns(filtered)
    filtered = deduplicate_messages(filtered)
    filtered = limit_relevant_rows(filtered)
    evidence = summarize_evidence(filtered, block_id)
    return filtered, evidence
