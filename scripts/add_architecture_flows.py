#!/usr/bin/env python3
"""Insert or update Architecture Flow (ASCII) cell in each presentation notebook.

GitHub notebook view does not render Mermaid — use plain-text flow diagrams instead.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CELL_MARKER = "## Architecture Flow"
CELL_ID = "architecture-flow"

FLOWS: dict[str, str] = {
    "series-2.1": """## Architecture Flow

Visual map of the context pruning pipeline — from user question to side-by-side benchmark.

```
User Question
     │
     ▼
 Ambiguous? ──Yes──► Clarifying questions (0 tokens) → EXIT
     │
    No
     ▼
 Load datasets/HDFS_2k.log (2,000 lines)
     │
     ├────────────────────────────┬────────────────────────────┐
     ▼                            ▼                            │
 FLOW A — Without pruning   FLOW B — With pruning              │
     │                            │                            │
     ▼                            ▼                            │
 build_unpruned_prompt()    prune.py                           │
 ~71,000 prompt tokens      filter → dedupe → cap → summarize  │
     │                            │                            │
     │                            ▼                            │
     │                     build_pruned_prompt()                │
     │                     ~200 prompt tokens                   │
     │                            │                            │
     └──────────────┬─────────────┘                            │
                    ▼                                          │
             Gemini API (or --dry-run)                         │
                    ▼                                          │
          common/benchmark.py                                  │
    tokens · latency · cost · savings                          │
```

### Component roles

| Component | Role |
|-----------|------|
| `app.py` | Orchestrates both flows and prints the benchmark |
| `prune.py` | Deterministic 5-step pruning pipeline |
| `common/prompt_builder.py` | Builds unpruned vs pruned prompts |
| `common/gemini_client.py` | LLM call with token counts |
| `common/benchmark.py` | Side-by-side comparison output |""",
    "series-2.2": """## Architecture Flow

Prompt caching splits each request into **static** (cacheable) and **dynamic** (per-request) layers. Evidence is still pruned first (Series 2.1).

```
User Question + Pruned HDFS evidence (series-2.1/prune.py)
     │
     ▼
 prompt_cache.py + prompt_builder.py
     │
     ├────────────────────────────┬────────────────────────────┐
     ▼                            ▼                            │
 STATIC layer (cacheable)    DYNAMIC layer (never cache)       │
 role · rules · schema       question + pruned evidence        │
     │                            │                            │
     ├──────────────┐             │                            │
     ▼              ▼             ▼                            │
 Flow A          Flow B       (always sent)                     │
 no cache       cache hit                                      │
 full static    discounted                                     │
 token cost     static billing                                 │
     │              │             │                            │
     └──────┬───────┴─────────────┘                            │
            ▼                                                  │
     Gemini API (or --dry-run)                                 │
            ▼                                                  │
     benchmark.py (+ 100-request cost projection)               │

 Prompt Cache (v1 / v2 / v3)  ◄── write on miss, read on hit
```

### Static vs dynamic

| Layer | Contents | Cache? |
|-------|----------|--------|
| **Static** | Role, investigation rules, schema, output format | Yes |
| **Dynamic** | User question, pruned log evidence | Never |""",
    "series-2.3": """## Architecture Flow

Controlled RAG experiment: same corpus, same questions, same model — only **chunking strategy** changes.

```
docs/ corpus (4 articles)
     │
     ▼
 chunker.py ──► small (200) │ medium (500) │ large (1000) │ semantic (# headings)
     │
     ▼
 retriever.py ◄── questions.py (benchmark queries + expected terms)
     │              keyword score + Hit Score
     ▼
 prompt_builder.py (top-K chunks + question)
     │
     ▼
 Gemini API (or --dry-run)
     │
     ▼
 benchmark.py — Hit Score · tokens · latency · cost
```

### Data flow per strategy

```
Documents → Chunk strategy → Retrieve top-K → Build RAG prompt → Gemini → Compare metrics
```

Each of the four chunk strategies runs this identical pipeline; only the chunk boundaries differ.""",
    "series-2.4": """## Architecture Flow

Conversation summarization compresses chat history **before** it reaches the model. Gemini never sees all 175 messages (except in the `full` baseline).

```
conversation_dataset.py (175 messages)
     │
     ▼
 Choose summarization strategy
     │
     ├── full          → all 175 messages in prompt
     ├── rolling       → summary + last 10 messages
     ├── hierarchical  → 20-msg blocks → master summary + last 10
     └── semantic      → structured facts + last 5 messages
     │
     ▼
 Compressed memory + recent messages
     │
     ▼
 prompts.py → Gemini API (or --dry-run)
     │
     ▼
 evaluator.py (Memory Score · Context Retention)
     │
     ▼
 benchmark.py (4-strategy comparison)
```

### Memory injection pattern

```
175 Messages → Summarizer → Conversation Memory + Latest Messages → Prompt → Gemini
```""",
    "series-2.5": """## Architecture Flow

Long-term memory pipeline: extract durable knowledge from 500 conversations, compress the store, retrieve only relevant memories for each question.

```
conversations.py (500 simulated chats)
     │
     ▼
 memory_extractor.py (category · key · value)
     │
     ▼
 Storage strategy
     ├── no compression        → store everything
     ├── deduplication         → same key → one record
     ├── full compression      → dedup · consolidate · update · expire
     └── compression + retrieval → top-K injection only
     │
     ▼
 memory_store.json (user profile)
     │
     ▼
 memory_retriever.py (intent + keyword top-K)  [compression + retrieval only]
     │
     ▼
 prompts.py → Gemini API (or --dry-run)
     │
     ▼
 evaluator.py → benchmark.py
```

### Compression operations

```
Extract → Dedup → Consolidate → Update stale → Expire temporary → Store → Retrieve top-K → Prompt
```""",
    "series-2.6": """## Architecture Flow

Memory retrieval from a 100,000-record store: intent detection → search → rank → inject top-K into the prompt.

```
memories.py + memory_store.py (100,000 records)
     │
     ▼
 Inverted index + TF-IDF vectors
     │
queries.py (benchmark query) → Intent detection
     │
     ▼
 Retrieval strategy
     ├── keyword        → exact term overlap
     ├── semantic       → TF-IDF cosine similarity
     ├── hybrid         → keyword + semantic + metadata
     └── hybrid+rerank  → top-20 candidates → score → top-K
     │
     ▼
 ranking.py (similarity + confidence + recency + priority)
     │
     ▼
 prompts.py → Gemini API (or --dry-run)
     │
     ▼
 evaluator.py (precision · recall · accuracy) → benchmark.py
```

### Ranking formula (re-ranking strategy)

```
Memory Score = Semantic Similarity + Confidence + Recency + Business Priority
```""",
    "series-2.7": """## Architecture Flow

Model routing sends each of 1,000 requests to the most cost-effective model tier — not the largest model every time.

```
requests.py (1,000 AI requests)
     │
     ▼
 classifier.py (intent + task type)
     │
     ▼
 complexity.py (simple · medium · complex)
     │
     ▼
 policy.py (security + budget rules)
     │
     ▼
 router.py — routing strategy
     ├── single      → all requests → Large General LLM
     ├── rules       → static task-type → model map
     ├── dynamic     → score by intent · cost · latency
     └── confidence  → cheap model first · escalate if needed
     │
     ▼
 models.py — Model Pool
   Small │ Medium Coding │ Internal │ Reasoning │ Vision │ Large General
     │
     ▼
 Execute request — Gemini (--live) or metadata estimate (--dry-run)
     │
     ▼
 evaluator.py → benchmark.py
```

### Routing pipeline

```
Request → Intent → Complexity → Policy → Router → Best Model → Response
```""",
    "series-2.8": """## Architecture Flow

Multi-agent orchestration: specialized agents coordinate through a **Shared Memory** bus — they never communicate directly.

```
tasks.py (Enterprise request)
     │
     ▼
 planner.py — Planner Agent (task decomposition)
     │
     ▼
 scheduler.py + orchestrator.py (strategy)
     ├── single      → one general agent
     ├── sequential  → agents in dependency order
     ├── parallel    → independent waves in parallel
     └── reviewer    → parallel + validation pass
     │
     ▼
 agents.py — Specialized Pool
   Architecture │ Backend │ Frontend │ Database
   Security │ Testing │ DevOps │ Documentation
     │
     ▼ read / write (no direct agent-to-agent calls)
 shared_memory.py — Shared Memory Bus
     │
     ▼
 Result Aggregator
     │
     ▼ optional
 reviewer.py — Reviewer Agent (gaps → one rework iteration)
     │
     ▼
 Final Response → evaluator.py → benchmark.py
```

### Coordination rule

```
Agents read/write Shared Memory only — no direct agent-to-agent messaging.
```""",
}


def to_source_list(text: str) -> list[str]:
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def series_key(path: Path) -> str | None:
    m = re.match(r"series-2\.\d+", path.parent.name)
    return m.group(0) if m else None


def find_cell_index(cells: list[dict], marker: str) -> int | None:
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        text = "".join(src) if isinstance(src, list) else src
        if marker in text:
            return i
    return None


def insert_after_index(cells: list[dict], after_marker: str) -> int:
    """Return index to insert new cell (after end-to-end scenario, else after title)."""
    idx = find_cell_index(cells, after_marker)
    if idx is not None:
        return idx + 1
    return 1


def patch_notebook(path: Path) -> str:
    key = series_key(path)
    if not key or key not in FLOWS:
        return f"SKIP {path.name} (no flow defined)"

    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    if not cells:
        return f"SKIP {path.name} (empty notebook)"

    new_cell = {
        "cell_type": "markdown",
        "id": CELL_ID,
        "metadata": {},
        "source": to_source_list(FLOWS[key]),
    }

    idx = find_cell_index(cells, CELL_MARKER)
    if idx is not None:
        cells[idx] = new_cell
        action = "updated"
    else:
        insert_at = insert_after_index(cells, "## End-to-End Scenario")
        cells.insert(insert_at, new_cell)
        action = "inserted"

    nb["cells"] = cells
    path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"{action.upper()} {path.relative_to(ROOT)}"


def main() -> int:
    notebooks = sorted(ROOT.glob("series-2.*/Series_*.ipynb"))
    if not notebooks:
        print("No notebooks found.", file=sys.stderr)
        return 1

    for nb_path in notebooks:
        print(patch_notebook(nb_path))

    print(f"\nPatched {len(notebooks)} notebook(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
