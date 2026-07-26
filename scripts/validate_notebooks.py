#!/usr/bin/env python3
"""
Validate presentation notebooks before commit/push.

Checks:
  - Valid JSON
  - nbformat schema (nbformat 4.x) — same rules GitHub uses
  - Cell source is list-of-strings (not bare string)
  - Cell IDs match ^[a-zA-Z0-9-_]+$

Usage:
  python scripts/validate_notebooks.py           # validate all
  python scripts/validate_notebooks.py --fix   # auto-fix source format + cell IDs
  python scripts/validate_notebooks.py path/to/notebook.ipynb
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CELL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9-_]+$")


def to_source_list(text: str) -> list[str]:
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def sanitize_cell_id(cell_id: str) -> str:
    """Replace characters invalid for nbformat cell IDs."""
    cleaned = re.sub(r"[^a-zA-Z0-9-_]", "-", cell_id)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "cell-id"


def discover_notebooks(explicit: list[str] | None) -> list[Path]:
    if explicit:
        return [Path(p).resolve() for p in explicit]
    return sorted(ROOT.glob("series-2.*/Series_*.ipynb"))


def fix_notebook(path: Path) -> list[str]:
    """Apply safe auto-fixes. Returns list of fix descriptions."""
    fixes: list[str] = []
    nb = json.loads(path.read_text(encoding="utf-8"))

    for i, cell in enumerate(nb.get("cells", [])):
        src = cell.get("source", "")
        if isinstance(src, str):
            cell["source"] = to_source_list(src)
            fixes.append(f"cell {i}: converted string source → line array")
        elif isinstance(src, list):
            joined = "".join(src)
            normalized = to_source_list(joined)
            if normalized != src:
                cell["source"] = normalized
                fixes.append(f"cell {i}: normalized source line endings")

        cell_id = cell.get("id")
        if cell_id and not CELL_ID_PATTERN.match(cell_id):
            new_id = sanitize_cell_id(cell_id)
            cell["id"] = new_id
            fixes.append(f"cell {i}: id '{cell_id}' → '{new_id}'")

    if fixes:
        path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return fixes


def validate_notebook(path: Path) -> list[str]:
    """Return list of error messages (empty = valid)."""
    errors: list[str] = []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if "cells" not in raw or not isinstance(raw["cells"], list):
        errors.append("missing or invalid 'cells' array")
        return errors

    for i, cell in enumerate(raw["cells"]):
        src = cell.get("source", "")
        if isinstance(src, str):
            errors.append(f"cell {i}: source must be a list of strings, not a bare string")
        elif isinstance(src, list) and not all(isinstance(line, str) for line in src):
            errors.append(f"cell {i}: source list contains non-string entries")

        cell_id = cell.get("id")
        if cell_id and not CELL_ID_PATTERN.match(cell_id):
            errors.append(
                f"cell {i}: id '{cell_id}' is invalid (must match ^[a-zA-Z0-9-_]+$)"
            )

    try:
        import nbformat
        from nbformat.validator import validate

        nbf = nbformat.from_dict(raw)
        validate(nbf)
    except ImportError:
        errors.append("warning: nbformat not installed — schema validation skipped (pip install nbformat)")
    except Exception as exc:
        errors.append(f"nbformat validation failed: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Series 2 presentation notebooks")
    parser.add_argument("notebooks", nargs="*", help="Notebook paths (default: all series-2.*/*.ipynb)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix source format and cell IDs")
    args = parser.parse_args()

    paths = discover_notebooks(args.notebooks or None)
    if not paths:
        print("No notebooks found.", file=sys.stderr)
        return 1

    exit_code = 0
    for path in paths:
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if args.fix:
            fixes = fix_notebook(path)
            for fix in fixes:
                print(f"FIX  {rel}: {fix}")

        errors = validate_notebook(path)
        hard_errors = [e for e in errors if not e.startswith("warning:")]
        warnings = [e for e in errors if e.startswith("warning:")]

        if hard_errors:
            exit_code = 1
            print(f"FAIL {rel}")
            for err in hard_errors:
                print(f"  - {err}")
        else:
            print(f"OK   {rel}")
            for warn in warnings:
                print(f"  ! {warn}")

    if exit_code:
        print("\nNotebook validation failed. Run with --fix or fix manually before pushing.", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
