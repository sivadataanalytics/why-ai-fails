#!/usr/bin/env python3
"""
Entry point for the context pruning demo.

  python demo.py --clarify-demo   # Layer 1: clarify first (0 tokens)
  python demo.py --dry-run        # Layer 2+3: compare token counts ($0)
  python demo.py                  # Full benchmark with Gemini API
"""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).parent / "series-2" / "2.1-context-pruning" / "app.py"),
    run_name="__main__",
)
