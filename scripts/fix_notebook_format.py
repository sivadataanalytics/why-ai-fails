#!/usr/bin/env python3
"""Normalize Jupyter notebook cell sources to list-of-strings format (GitHub-compatible)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def to_source_list(text: str) -> list[str]:
    """Convert cell source to Jupyter line array (each line ends with \\n)."""
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    if not lines:
        return [text]
    # Ensure final line has newline — matches original Series 2.1 notebooks
    if not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def normalize_notebook(path: Path) -> bool:
    nb = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for cell in nb["cells"]:
        src = cell.get("source", "")
        if isinstance(src, str):
            cell["source"] = to_source_list(src)
            changed = True
        elif isinstance(src, list) and src and all(isinstance(x, str) for x in src):
            joined = "".join(src)
            normalized = to_source_list(joined)
            if normalized != src:
                cell["source"] = normalized
                changed = True
    if changed:
        path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    for path in sorted(ROOT.glob("series-2.*/Series_*.ipynb")):
        if normalize_notebook(path):
            print(f"Fixed {path.relative_to(ROOT)}")
        else:
            print(f"OK    {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
