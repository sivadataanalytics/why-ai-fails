#!/usr/bin/env python3
"""Insert or update End-to-End Scenario summary cell in each presentation notebook."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CELL_MARKER = "## End-to-End Scenario"
CELL_ID = "end-to-end-scenario"

SUMMARIES: dict[str, str] = {
    "series-2.1": """## End-to-End Scenario

**What this lab does from start to finish**

You are on-call for an HDFS incident. A block failed overnight and leadership wants a root-cause summary before the morning standup. This notebook walks through the full engineering flow — from a vague user question to a side-by-side token benchmark.

### Step-by-step flow

1. **Receive the question** — e.g. *"Investigate why HDFS block blk_-8775602795571523802 failed."*
2. **Clarify first (Layer 1)** — if the question is vague, the app asks scoping questions and spends **0 tokens** on logs until scope is known.
3. **Load evidence** — read `datasets/HDFS_2k.log` (2,000 synthetic log lines).
4. **Run Flow A — without pruning** — dump the entire log into the prompt via `build_unpruned_prompt()` → ~**71,000+** input tokens → call Gemini (or `--dry-run` simulation).
5. **Run Flow B — with pruning** — `prune.py` pipeline:
   - filter lines by block ID
   - drop unused columns
   - deduplicate repeated messages
   - cap rows (ERROR/WARN first)
   - summarize into a compact evidence block
   - `build_pruned_prompt()` → ~**200** input tokens → same Gemini call
6. **Compare results** — `benchmark.py` prints prompt tokens, latency, estimated cost, and **~99% savings** for the same model and same question.
7. **Live demo cell** — run `python series-2.1/app.py --dry-run` from this notebook to reproduce the benchmark with no API key.

### What you should observe

| Stage | Without pruning | With pruning |
|-------|-----------------|--------------|
| Evidence in prompt | All 2,000 lines | Block-scoped summary |
| Prompt tokens | ~71,000+ | ~200 |
| Answer quality | Baseline | Same question, same model |
| Engineering win | — | Deterministic pre-call filtering |

**Takeaway:** Context pruning happens **before** the LLM call. You pay for fewer tokens and get faster responses without changing the model.""",
    "series-2.2": """## End-to-End Scenario

**What this lab does from start to finish**

Series 2.1 showed how to shrink **evidence**. This lab shows how to stop re-billing the **same system instructions** on every investigation. You run the same HDFS block failure scenario — but now across many repeated requests where the static prompt never changes.

### Step-by-step flow

1. **Start from pruned evidence** — reuse Series 2.1's `prune.py` so the dynamic half of the prompt stays small (~200 tokens of log evidence).
2. **Split the prompt into two layers:**
   - **Static (cacheable):** assistant role, investigation rules, dataset schema, output format — built by `build_static_prompt()` in `prompt_cache.py`
   - **Dynamic (never cache):** user question + pruned evidence — built by `build_dynamic_prompt()` in `common/prompt_builder.py`
3. **Run Flow A — without caching** — every request sends static + dynamic; Gemini (or dry-run) bills the **full static token cost** each time (~510 tokens for v1).
4. **Run Flow B — with caching** — first request writes static prompt to cache; subsequent requests get a **cache hit** and static tokens are billed at the **discounted cached rate** (~156 effective prompt tokens).
5. **Project at scale** — `benchmark.py` extrapolates savings across **100 requests** to show compounding cost reduction in production.
6. **Knowledge drift demo (optional)** — run `--drift-demo` to compare static prompt versions v1 → v2 → v3 and see when the cache must invalidate.
7. **Live demo cell** — run `python series-2.2/app.py --dry-run` to print the side-by-side comparison.

### What you should observe

| Stage | Without caching | With caching (hit) |
|-------|-----------------|---------------------|
| Static prompt | Re-processed every call | Read from cache |
| Prompt tokens (v1) | ~510 | ~156 |
| Answer quality | Baseline | Unchanged |
| At 100 requests | Full static cost × 100 | Static cost × 1 + hits × discount |

**Takeaway:** Cache **stable** instructions. Never cache **per-request** evidence. Series 2.1 + 2.2 stack: prune first, then cache the shell.""",
    "series-2.3": """## End-to-End Scenario

**What this lab does from start to finish**

Your team deployed a RAG assistant over internal documentation. Retrieval quality is inconsistent and the prompt bill is climbing. This lab runs a controlled experiment: **same corpus, same questions, same model** — only the chunking strategy changes.

### Step-by-step flow

1. **Load the document corpus** — four `.txt` articles under `docs/` (Hidden Economics, Context Pruning, Prompt Caching, RAG Chunking).
2. **Pick a chunking strategy** — `small` (200 tokens), `medium` (500), `large` (1000), or `semantic` (split on `#` headings) via `chunker.py`.
3. **Split documents into chunks** — each strategy produces a different set of retrievable evidence units.
4. **Run benchmark questions** — `questions.py` defines queries with **expected terms** (ground truth for retrieval quality).
5. **Retrieve top-K chunks** — `retriever.py` keyword-scores chunks and computes **Hit Score** = matched expected terms / total expected terms.
6. **Build the RAG prompt** — `prompt_builder.py` injects retrieved chunks + user question.
7. **Call Gemini** — live API or `--dry-run` simulation records prompt tokens, latency, and estimated cost.
8. **Repeat for all four strategies** — `benchmark.py` prints a side-by-side table: Hit Score vs prompt tokens vs cost.
9. **Live demo cell** — run `python series-2.3/app.py --dry-run` to see which chunk size wins on **your** corpus.

### What you should observe

| Strategy | Typical tradeoff |
|----------|------------------|
| `small` | Lowest prompt cost; may miss cross-section context |
| `medium` | Often best balance for documentation-style corpora |
| `large` | Higher Hit Score sometimes; always higher token bill |
| `semantic` | Respects document structure when headings are meaningful |

**Takeaway:** Chunk size is the first lever in RAG economics. Benchmark on real questions — don't copy framework defaults.""",
    "series-2.4": """## End-to-End Scenario

**What this lab does from start to finish**

An enterprise AI coding assistant has been pair-programming with a developer for weeks. The conversation now has **175 messages** — preferences, architecture decisions, pending tasks, and a lot of "thanks" and "good morning." Every new turn replays the entire thread. This lab shows how to compress that history without losing what matters.

### Step-by-step flow

1. **Load the conversation** — `conversation_dataset.py` provides ~175 synthetic messages spanning a realistic coding-assistant thread (Python preference, Prompt Caching project, summarization strategies, pending benchmarks, architecture decisions).
2. **Define benchmark questions** — e.g. *"What language does the user prefer?"*, *"What summarization strategies were discussed?"* — each with **expected facts** the model must remember.
3. **Run four summarization strategies:**
   - **Full** — send all 175 messages (baseline; highest cost, perfect memory)
   - **Rolling** — rolling summary + latest 10 messages
   - **Hierarchical** — summarize in 20-message blocks → master summary + latest 10
   - **Semantic** — extract structured facts only + latest 5 messages
4. **Build the prompt** — `prompts.py` combines compressed memory + recent messages; Gemini never sees the full transcript (except in `full` baseline).
5. **Answer benchmark questions** — Gemini responds (or dry-run simulates).
6. **Evaluate memory** — `evaluator.py` computes **Memory Score** (remembered facts / expected facts) and **Context Retention** relative to the full conversation.
7. **Compare strategies** — `benchmark.py` prints prompt tokens, summary size, Memory Score, latency, and cost side by side.
8. **Live demo cell** — run `python series-2.4/app.py --dry-run`.

### What you should observe

| Strategy | Prompt size | Memory Score | Best for |
|----------|-------------|--------------|----------|
| Full | Largest (175 msgs) | 1.0 (baseline) | Reference only |
| Rolling | Much smaller | High | Most chat apps |
| Hierarchical | Bounded | High | Very long threads |
| Semantic | Smallest | High density | Fact-heavy assistants |

**Takeaway:** Summarization is **memory management**, not just token trimming. The goal is to remember decisions and preferences — not every message.""",
    "series-2.5": """## End-to-End Scenario

**What this lab does from start to finish**

A personal AI assistant has chatted with a user across **500 conversations** over months. Storing every message is impossible; storing every extracted fact without compression creates an unbounded memory store. This lab builds a **compressed long-term memory profile** and measures how much you can shrink it while still answering correctly.

### Step-by-step flow

1. **Load 500 simulated conversations** — `conversations.py` covers coding preferences, project history, tools, and temporary notes.
2. **Extract structured memories** — `memory_extractor.py` pulls category + key + value records (e.g. Language → Python, IDE → VS Code).
3. **Run four storage strategies:**
   - **No compression** — store every extracted memory (largest store and prompt)
   - **Deduplication** — same category+key → single memory
   - **Full compression** — dedup + consolidate related entries + update stale values + expire low-confidence/temporary items
   - **Compression + retrieval** — compressed store + inject only **top-K relevant** memories into the prompt
4. **Persist the profile** — `memory_store.py` writes a JSON user memory file.
5. **Answer benchmark questions** — `memory_retriever.py` finds relevant memories by intent + keyword; `prompts.py` injects them into the Gemini prompt.
6. **Evaluate retrieval** — `evaluator.py` measures whether the right memories were found and used.
7. **Compare all four strategies** — `benchmark.py` shows store size, prompt tokens, retrieval accuracy, and cost.
8. **Live demo cell** — run `python series-2.5/app.py --dry-run`.

### What you should observe

| Strategy | Memory store | Prompt injection | Tradeoff |
|----------|--------------|------------------|----------|
| No compression | Largest | All memories | Simple but unbounded |
| Dedup | Smaller | All unique memories | Removes duplicates only |
| Full compression | Much smaller | All compressed | Consolidates + expires |
| Compression + retrieval | Smallest store | Top-K only | Best production pattern |

**Takeaway:** Long-term memory is a **compressed knowledge base**, not a conversation archive. Extract → compress → retrieve only what's relevant.""",
    "series-2.6": """## End-to-End Scenario

**What this lab does from start to finish**

Series 2.5 showed how to **build and compress** long-term memory. Now the assistant has **100,000 memory records** — user profiles, org policies, project knowledge, coding preferences, security rules, and noise (obsolete Flask entries, conflicting IDE preferences). A user asks a question. Can the system find the **right** memories in milliseconds?

### Step-by-step flow

1. **Load the memory store** — `memories.py` generates 100k synthetic records across seven categories with duplicates, noise, and obsolete entries.
2. **Index for search** — `memory_store.py` builds an inverted index (keyword) and TF-IDF vectors (semantic).
3. **Receive a benchmark query** — `queries.py` defines questions with expected memory IDs (ground truth).
4. **Detect intent** — classify what kind of memory the user needs (profile, policy, project, etc.).
5. **Run one of four retrieval strategies:**
   - **Keyword** — inverted index, exact term overlap (fast baseline)
   - **Semantic** — TF-IDF cosine similarity (related concepts)
   - **Hybrid** — keyword + semantic + metadata (enterprise baseline)
   - **Hybrid + Re-ranking** — top-20 hybrid candidates → ranking formula → final top-K
6. **Rank and select top-K** — `ranking.py` scores by semantic similarity + confidence + recency + business priority.
7. **Build the prompt** — inject selected memories via `prompts.py` → Gemini answers (or dry-run).
8. **Evaluate** — `evaluator.py` reports precision, recall, and accuracy against expected memory IDs.
9. **Benchmark all strategies** — `benchmark.py` compares retrieval quality vs latency vs prompt size.
10. **Live demo cell** — run `python series-2.6/app.py --dry-run`.

### What you should observe

| Strategy | Speed | Handles synonyms | Production fit |
|----------|-------|------------------|----------------|
| Keyword | Fastest | No | Simple lookups |
| Semantic | Medium | Yes | Conceptual questions |
| Hybrid | Medium | Yes | Default enterprise choice |
| Re-rank | Slower | Yes + priority | Highest accuracy |

**Takeaway:** Building memory is half the problem. **Retrieving the right memory at the right time** is what makes AI feel intelligent.""",
    "series-2.7": """## End-to-End Scenario

**What this lab does from start to finish**

Your enterprise AI platform routes every employee request through a single large LLM — translation, SQL generation, architecture reviews, image analysis, all at premium cost. This lab processes **1,000 synthetic requests** through four routing strategies and shows how much cost and latency you save by sending each task to the **right-sized model**.

### Step-by-step flow

1. **Load the request queue** — `requests.py` generates 1,000 diverse AI requests (translation, classification, SQL, API code, architecture, legal, vision, etc.).
2. **Classify each request** — `classifier.py` detects **intent** and **task type**.
3. **Estimate complexity** — `complexity.py` labels each request simple / medium / complex.
4. **Apply policies** — `policy.py` enforces security rules (e.g. confidential code → internal model only) and budget constraints.
5. **Route to a model** — `router.py` picks from the model pool in `models.py`:
   - Small Language Model, Medium Coding Model, Medium Coding (Internal), Large Reasoning Model, Vision Model, Large General LLM (baseline)
6. **Run one of four routing strategies:**
   - **Single** — everything → large general LLM (baseline; highest cost)
   - **Rules** — static task-type → model map
   - **Dynamic** — score models on intent, complexity, cost, latency
   - **Confidence** — start with cheapest capable model; escalate only if confidence is low
7. **Execute the request** — live Gemini call or `--dry-run` simulation with model-specific latency/cost.
8. **Evaluate routing** — `evaluator.py` measures routing accuracy, model utilization, escalation rate, total cost, and average latency.
9. **Compare all strategies** — `benchmark.py` prints side-by-side metrics across 1,000 requests.
10. **Live demo cell** — run `python series-2.7/app.py --dry-run`.

### What you should observe

| Strategy | Cost vs single | Routing accuracy | Best for |
|----------|----------------|------------------|----------|
| Single | 1.0× (baseline) | N/A | Simplicity |
| Rules | Lower | Good for known patterns | Stable workloads |
| Dynamic | Lower | Adapts to complexity | Mixed workloads |
| Confidence | Lowest | Escalates when needed | Cost-sensitive prod |

**Takeaway:** Enterprise AI efficiency comes from **selecting the right model per request** — not running the biggest model every time.""",
    "series-2.8": """## End-to-End Scenario

**What this lab does from start to finish**

A product manager submits an enterprise software request: *"Design and build a secure REST API for inventory management with authentication, database schema, tests, and deployment docs."* One general-purpose agent would produce a shallow answer. This lab coordinates **ten specialized agents** through a planner, scheduler, shared memory bus, and optional reviewer — across **500 benchmark requests**.

### Step-by-step flow

1. **Receive an enterprise request** — `tasks.py` provides 500 requests across 8 categories (greenfield apps, API design, security audits, migrations, etc.).
2. **Plan the work** — **Planner Agent** (`planner.py`) decomposes the request into domain tasks with dependencies (architecture → backend → database → security → tests → docs).
3. **Schedule execution** — `scheduler.py` runs tasks **sequentially** (one after another) or in **parallel waves** (independent tasks simultaneously).
4. **Execute with specialized agents** — `agents.py` pool:
   - Architecture, Backend, Frontend, Database, Security, Testing, DevOps, Documentation (+ Planner, Reviewer)
   - Each agent reads context from and writes outputs to **SharedMemory** (`shared_memory.py`) — agents never talk directly to each other.
5. **Aggregate results** — `orchestrator.py` merges agent outputs into a unified deliverable.
6. **Optional review pass** — **Reviewer Agent** (`reviewer.py`) checks consistency, finds gaps, and triggers **one rework iteration** if needed.
7. **Run four orchestration strategies:**
   - **Single** — one general agent handles everything
   - **Sequential** — planner → agents in dependency order
   - **Parallel** — independent agents in parallel waves
   - **Parallel + Reviewer** — parallel execution + validation pass
8. **Evaluate output** — `evaluator.py` scores quality, consistency, and task completion (computed metrics).
9. **Benchmark all strategies** — `benchmark.py` compares latency, quality, and completion rate.
10. **Live demo cell** — run `python series-2.8/app.py --dry-run --requests 50`.

### What you should observe

| Strategy | Typical pattern |
|----------|-----------------|
| Single | One agent, lower task completion |
| Sequential | Full domain depth, higher latency |
| Parallel | Fastest wall-clock, strong completion |
| Parallel + Reviewer | Review + rework → highest quality |

**Takeaway:** One intelligent agent can **answer**. A coordinated team of specialized agents — with a planner, scheduler, shared memory, and reviewer — can **build**.""",
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


def find_scenario_cell_index(cells: list[dict]) -> int | None:
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        text = "".join(src) if isinstance(src, list) else src
        if CELL_MARKER in text:
            return i
    return None


def patch_notebook(path: Path) -> str:
    key = series_key(path)
    if not key or key not in SUMMARIES:
        return f"SKIP {path.name} (no summary defined)"

    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    if not cells:
        return f"SKIP {path.name} (empty notebook)"

    new_cell = {
        "cell_type": "markdown",
        "id": CELL_ID,
        "metadata": {},
        "source": to_source_list(SUMMARIES[key]),
    }

    idx = find_scenario_cell_index(cells)
    if idx is not None:
        cells[idx] = new_cell
        action = "updated"
    else:
        # Insert after title cell (index 0), before "## 1. The Problem"
        cells.insert(1, new_cell)
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
