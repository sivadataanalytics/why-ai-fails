#!/usr/bin/env python3
# Entry point: python demo.py [--dry-run] [--clarify-demo]

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).parent / "series-2" / "2.1-context-pruning" / "app.py"),
    run_name="__main__",
)
