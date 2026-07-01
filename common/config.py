"""
Configuration — paths, defaults, API key.

DEFAULT_LOG_FILE  — 2000-line HDFS sample; unpruned flow sends all lines to Gemini
DEFAULT_QUESTION  — includes a block ID so pruning can filter effectively
AMBIGUOUS_QUESTION — demo for clarify-first flow (0 tokens)
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT_DIR / "datasets"
DEFAULT_LOG_FILE = DATASETS_DIR / "HDFS_2k.log"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Block ID present in HDFS_2k.log — pruning filters 2000 lines down to ~2
DEFAULT_BLOCK_ID = "blk_-8775602795571523802"
DEFAULT_QUESTION = f"Investigate why HDFS block {DEFAULT_BLOCK_ID} failed."

# Used by --clarify-demo to show zero-token scoping step
AMBIGUOUS_QUESTION = "Investigate the issue."


def load_config() -> None:
    load_dotenv(ROOT_DIR / ".env")


def get_api_key() -> str:
    load_config()
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("Missing GEMINI_API_KEY in .env (from aistudio.google.com/apikey)")
    return key
