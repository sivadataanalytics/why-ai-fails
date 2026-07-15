# Series 2.1 — Context Pruning

**Engineering Lab:** reduce prompt size by sending only the log evidence the model needs.

Organizations pay for **tokens**, not API calls. Dumping 2,000 HDFS log lines into every request costs ~71,000+ input tokens. Context pruning filters that down to ~200 tokens for the same investigation question.

## What this demo proves

| Without pruning | With pruning |
|-----------------|--------------|
| All 2,000 log lines in the prompt | Filter by block ID → dedupe → summarize |
| ~71,000+ prompt tokens | ~200 prompt tokens |
| Slow, expensive | Fast, cheap |
| Same model, same question | Same model, same question |

## Three layers of token savings

1. **Clarify first** — vague questions get scoping questions; **0 tokens** spent on logs
2. **Prune context** — `prune.py` removes irrelevant lines before building the prompt
3. **Measure** — side-by-side benchmark shows exact token and latency reduction

## Files

```
series-2.1/
  app.py      Main entry — runs without vs with pruning, prints benchmark
  prune.py    5-step pipeline: filter → columns → dedupe → cap → summarize
  README.md   This file
```

**Shared (repo root):**

- `common/prompt_builder.py` — `build_unpruned_prompt()` vs `build_pruned_prompt()`
- `common/benchmark.py` — prints savings comparison
- `common/gemini_client.py` — Gemini API wrapper with token counts
- `datasets/HDFS_2k.log` — sample dataset

## Pruning pipeline (`prune.py`)

```
2000 log lines
  → filter by block ID        (~2 lines)
  → drop unused columns
  → deduplicate messages
  → cap rows (ERROR/WARN first)
  → summarize into evidence dict
  → ~200 tokens in final prompt
```

## Setup

From the repo root:

```bash
pip install -r requirements.txt
cp .env.example .env   # optional for live API runs
```

## Run

```bash
# Clarify-first demo — no logs loaded, 0 tokens
python demo.py --clarify-demo

# Token comparison only — no API call, $0
python demo.py --dry-run

# Full benchmark with Gemini
python demo.py

# Or run this folder directly
python series-2.1/app.py --dry-run
python series-2.1/app.py --question "Investigate why HDFS block blk_-8775602795571523802 failed."
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Estimate tokens locally; no Gemini call |
| `--clarify-demo` | Show clarify-first flow only |
| `--question` | Investigation question (must include a block ID) |
| `--log-file` | Path to HDFS log file (default: `datasets/HDFS_2k.log`) |

## Expected output (dry-run)

```
WITHOUT PRUNING   →  ~71,000 prompt tokens
WITH PRUNING      →  ~200 prompt tokens
SAVINGS           →  ~99% prompt reduction
```

## Next lab

[Series 2.2 — Prompt Caching](../series-2.2/) — after pruning evidence, cache the **static** system prompt so it is not re-processed on every request.
