#!/usr/bin/env python3
"""Insert or update Architecture Flow (Mermaid) cell in each presentation notebook."""

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

```mermaid
flowchart TB
    subgraph input["Input"]
        U["User Question"]
        LOG["datasets/HDFS_2k.log<br/>2,000 log lines"]
    end

    U --> CLARIFY{"Ambiguous<br/>question?"}
    CLARIFY -->|"Yes"| ZERO["Clarifying questions<br/>0 tokens spent"]
    CLARIFY -->|"No"| LOG

    LOG --> PATHA["Flow A — Without pruning"]
    LOG --> PATHB["Flow B — With pruning"]

    PATHA --> UNPR["build_unpruned_prompt()<br/>~71,000 tokens"]
    PATHB --> PRUNE["prune.py<br/>filter → dedupe → cap → summarize"]
    PRUNE --> PRUNED["build_pruned_prompt()<br/>~200 tokens"]

    UNPR --> GEMINI["Gemini API<br/>(or --dry-run)"]
    PRUNED --> GEMINI

    GEMINI --> BENCH["common/benchmark.py<br/>tokens · latency · cost · savings"]

    style PATHB fill:#e8f5e9
    style PRUNED fill:#c8e6c9
    style PATHA fill:#ffebee
    style UNPR fill:#ffcdd2
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

```mermaid
flowchart TB
    subgraph input["Input"]
        U["User Question"]
        LOG["Pruned HDFS evidence<br/>via series-2.1/prune.py"]
    end

    U --> BUILD
    LOG --> BUILD

    BUILD["prompt_cache.py + prompt_builder.py"]

    BUILD --> STATIC["Static layer<br/>role · rules · schema · format<br/>CACHEABLE"]
    BUILD --> DYNAMIC["Dynamic layer<br/>question + pruned evidence<br/>NEVER CACHE"]

    STATIC --> MISS["Flow A — Cache miss / no cache<br/>full static token cost"]
    STATIC --> HIT["Flow B — Cache hit<br/>discounted static billing"]

    DYNAMIC --> MISS
    DYNAMIC --> HIT

    MISS --> GEMINI["Gemini API<br/>(or --dry-run)"]
    HIT --> GEMINI

    GEMINI --> BENCH["benchmark.py<br/>per-request + 100-request projection"]

    CACHE[("Prompt Cache<br/>v1 / v2 / v3")]
    STATIC -.->|"write on miss"| CACHE
    CACHE -.->|"read on hit"| HIT

    style STATIC fill:#e3f2fd
    style DYNAMIC fill:#fff3e0
    style HIT fill:#e8f5e9
    style MISS fill:#ffebee
```

### Static vs dynamic

| Layer | Contents | Cache? |
|-------|----------|--------|
| **Static** | Role, investigation rules, schema, output format | Yes |
| **Dynamic** | User question, pruned log evidence | Never |""",
    "series-2.3": """## Architecture Flow

Controlled RAG experiment: same corpus, same questions, same model — only **chunking strategy** changes.

```mermaid
flowchart TB
    DOCS["docs/ corpus<br/>4 article files"] --> CHUNKER["chunker.py"]

    CHUNKER --> S1["small · 200 tokens"]
    CHUNKER --> S2["medium · 500 tokens"]
    CHUNKER --> S3["large · 1000 tokens"]
    CHUNKER --> S4["semantic · # headings"]

    S1 --> RET["retriever.py<br/>keyword score + Hit Score"]
    S2 --> RET
    S3 --> RET
    S4 --> RET

    Q["questions.py<br/>benchmark queries + expected terms"] --> RET

    RET --> PROMPT["prompt_builder.py<br/>top-K chunks + question"]
    PROMPT --> GEMINI["Gemini API<br/>(or --dry-run)"]
    GEMINI --> BENCH["benchmark.py<br/>Hit Score · tokens · latency · cost"]

    style CHUNKER fill:#e3f2fd
    style RET fill:#fff3e0
    style BENCH fill:#e8f5e9
```

### Data flow per strategy

```
Documents → Chunk strategy → Retrieve top-K → Build RAG prompt → Gemini → Compare metrics
```

Each of the four chunk strategies runs this identical pipeline; only the chunk boundaries differ.""",
    "series-2.4": """## Architecture Flow

Conversation summarization compresses chat history **before** it reaches the model. Gemini never sees all 175 messages (except in the `full` baseline).

```mermaid
flowchart TB
    CONV["conversation_dataset.py<br/>175 messages"] --> STRAT{"Summarization<br/>strategy"}

    STRAT --> FULL["full<br/>all 175 messages"]
    STRAT --> ROLL["rolling<br/>summary + last 10"]
    STRAT --> HIER["hierarchical<br/>20-msg blocks → master + last 10"]
    STRAT --> SEM["semantic<br/>structured facts + last 5"]

    FULL --> MEM["Compressed memory"]
    ROLL --> MEM
    HIER --> MEM
    SEM --> MEM

    MEM --> PROMPT["prompts.py<br/>memory + recent messages"]
    PROMPT --> GEMINI["Gemini API<br/>(or --dry-run)"]
    GEMINI --> EVAL["evaluator.py<br/>Memory Score · Context Retention"]
    EVAL --> BENCH["benchmark.py<br/>4-strategy comparison"]

    style FULL fill:#ffebee
    style ROLL fill:#e8f5e9
    style HIER fill:#e8f5e9
    style SEM fill:#c8e6c9
```

### Memory injection pattern

```
175 Messages → Summarizer → Conversation Memory + Latest Messages → Prompt → Gemini
```""",
    "series-2.5": """## Architecture Flow

Long-term memory pipeline: extract durable knowledge from 500 conversations, compress the store, retrieve only relevant memories for each question.

```mermaid
flowchart TB
    CONV["conversations.py<br/>500 simulated chats"] --> EXTRACT["memory_extractor.py<br/>category · key · value"]

    EXTRACT --> STRAT{"Storage<br/>strategy"}

    STRAT --> NC["no compression<br/>store everything"]
    STRAT --> DD["deduplication<br/>same key → one record"]
    STRAT --> FC["full compression<br/>dedup · consolidate · update · expire"]
    STRAT --> CR["compression + retrieval<br/>top-K injection only"]

    NC --> STORE[("memory_store.json<br/>user profile")]
    DD --> STORE
    FC --> STORE
    CR --> STORE

    STORE --> RET{"Retrieve?"}
    RET -->|"all strategies except CR"| PROMPT["prompts.py"]
    RET -->|"CR only"| RETR["memory_retriever.py<br/>intent + keyword top-K"]
    RETR --> PROMPT

    PROMPT --> GEMINI["Gemini API<br/>(or --dry-run)"]
    GEMINI --> EVAL["evaluator.py<br/>retrieval accuracy"]
    EVAL --> BENCH["benchmark.py"]

    style FC fill:#e8f5e9
    style CR fill:#c8e6c9
    style NC fill:#ffebee
```

### Compression operations

```
Extract → Dedup → Consolidate → Update stale → Expire temporary → Store → Retrieve top-K → Prompt
```""",
    "series-2.6": """## Architecture Flow

Memory retrieval from a 100,000-record store: intent detection → search → rank → inject top-K into the prompt.

```mermaid
flowchart TB
    STORE["memories.py + memory_store.py<br/>100,000 records"] --> IDX["Inverted index<br/>+ TF-IDF vectors"]

    QUERY["queries.py<br/>benchmark query"] --> INTENT["Intent detection"]

    INTENT --> STRAT{"Retrieval<br/>strategy"}

    STRAT --> KW["keyword<br/>exact term overlap"]
    STRAT --> SEM["semantic<br/>TF-IDF cosine"]
    STRAT --> HYB["hybrid<br/>keyword + semantic + metadata"]
    STRAT --> RR["hybrid + rerank<br/>top-20 → score → top-K"]

    IDX --> KW
    IDX --> SEM
    IDX --> HYB
    IDX --> RR

    KW --> RANK["ranking.py<br/>similarity + confidence + recency + priority"]
    SEM --> RANK
    HYB --> RANK
    RR --> RANK

    RANK --> PROMPT["prompts.py<br/>inject selected memories"]
    PROMPT --> GEMINI["Gemini API<br/>(or --dry-run)"]
    GEMINI --> EVAL["evaluator.py<br/>precision · recall · accuracy"]
    EVAL --> BENCH["benchmark.py"]

    style HYB fill:#e3f2fd
    style RR fill:#c8e6c9
```

### Ranking formula (re-ranking strategy)

```
Memory Score = Semantic Similarity + Confidence + Recency + Business Priority
```""",
    "series-2.7": """## Architecture Flow

Model routing sends each of 1,000 requests to the most cost-effective model tier — not the largest model every time.

```mermaid
flowchart TB
    REQ["requests.py<br/>1,000 AI requests"] --> CLASS["classifier.py<br/>intent + task type"]
    CLASS --> COMP["complexity.py<br/>simple · medium · complex"]
    COMP --> POL["policy.py<br/>security + budget rules"]
    POL --> ROUTER{"router.py<br/>strategy"}

    ROUTER --> SINGLE["single<br/>all → Large General LLM"]
    ROUTER --> RULES["rules<br/>static task → model map"]
    ROUTER --> DYN["dynamic<br/>score by intent · cost · latency"]
    ROUTER --> CONF["confidence<br/>cheap first · escalate if needed"]

    SINGLE --> POOL["models.py — Model Pool"]
    RULES --> POOL
    DYN --> POOL
    CONF --> POOL

    POOL --> SLM["Small Language Model"]
    POOL --> MCM["Medium Coding Model"]
    POOL --> MCI["Medium Coding Internal"]
    POOL --> LRM["Large Reasoning Model"]
    POOL --> VIS["Vision Model"]
    POOL --> LGL["Large General LLM"]

    SLM --> EXEC["Execute request<br/>Gemini or --dry-run"]
    MCM --> EXEC
    MCI --> EXEC
    LRM --> EXEC
    VIS --> EXEC
    LGL --> EXEC

    EXEC --> EVAL["evaluator.py<br/>accuracy · cost · escalation rate"]
    EVAL --> BENCH["benchmark.py"]

    style SINGLE fill:#ffebee
    style CONF fill:#c8e6c9
    style DYN fill:#e8f5e9
```

### Routing pipeline

```
Request → Intent → Complexity → Policy → Router → Best Model → Response
```""",
    "series-2.8": """## Architecture Flow

Multi-agent orchestration: specialized agents coordinate through a **Shared Memory** bus — they never communicate directly.

```mermaid
flowchart TB
    REQ["tasks.py<br/>Enterprise request"] --> PLAN["planner.py<br/>Planner Agent<br/>task decomposition"]

    PLAN --> SCHED["scheduler.py"]
    SCHED --> STRAT{"orchestrator.py<br/>strategy"}

    STRAT --> SINGLE["single<br/>one general agent"]
    STRAT --> SEQ["sequential<br/>dependency order"]
    STRAT --> PAR["parallel<br/>independent waves"]
    STRAT --> REV["parallel + reviewer<br/>validation pass"]

    SEQ --> AGENTS["agents.py — Specialized Pool"]
    PAR --> AGENTS
    REV --> AGENTS

    AGENTS --> ARCH["Architecture"]
    AGENTS --> BE["Backend"]
    AGENTS --> FE["Frontend"]
    AGENTS --> DB["Database"]
    AGENTS --> SEC["Security"]
    AGENTS --> TEST["Testing"]
    AGENTS --> OPS["DevOps"]
    AGENTS --> DOC["Documentation"]

    ARCH --> SM[("shared_memory.py<br/>Shared Memory Bus")]
    BE --> SM
    FE --> SM
    DB --> SM
    SEC --> SM
    TEST --> SM
    OPS --> SM
    DOC --> SM

    SM --> AGG["Result Aggregator"]
    REV --> REVIEW["reviewer.py<br/>Reviewer Agent"]
    REVIEW -->|"gaps found"| AGENTS
    REVIEW --> AGG
    SINGLE --> OUT["Final Response"]
    AGG --> OUT

    OUT --> EVAL["evaluator.py<br/>quality · consistency · completion"]
    EVAL --> BENCH["benchmark.py"]

    style SM fill:#e3f2fd
    style REV fill:#c8e6c9
    style SINGLE fill:#ffebee
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
