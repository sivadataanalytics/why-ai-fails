# Series 2.2 — Prompt Caching

**Engineering Lab:** avoid re-processing stable context on every request.

Unlike [Series 2.1](../series-2.1/), this lab is **not** about shrinking evidence. It is about not re-sending and re-billing the same system prompt, rules, and schema on every call.

## Static vs dynamic prompts

Every request is built from two layers:

```
┌─────────────────────────────────────┐
│  STATIC (cacheable)                 │  role, rules, schema, output format
│  build_static_prompt()              │  same every investigation
├─────────────────────────────────────┤
│  DYNAMIC (never cache)              │  user question + pruned evidence
│  build_dynamic_prompt()             │  changes every request
└─────────────────────────────────────┘
```

| Cacheable (static) | Never cache (dynamic) |
|--------------------|------------------------|
| Assistant role | User question |
| Investigation rules | Filtered log evidence |
| Dataset schema | Conversation history |
| Output format | Per-request diagnostics |

## What this demo proves

| Without caching | With caching (hit) |
|-----------------|------------------|
| Static + dynamic processed every time | Static read from cache |
| Full static token cost each request | Static billed at discounted rate |
| Same answer quality | Same answer quality |

Caching savings **compound** — the benchmark includes a **100-request** cost projection.

## Files

```
series-2.2/
  app.py            Main entry — without vs with cache, one Gemini call
  prompt_cache.py   Cache store, static prompt versions (v1/v2/v3), hit/miss
  benchmark.py      Prints side-by-side metrics and savings
  README.md         This file
```

**Reused from Series 2.1:**

- `series-2.1/prune.py` — evidence is still pruned before building the dynamic prompt

**Shared (repo root):**

- `common/prompt_builder.py` — `build_dynamic_prompt()`, `build_full_prompt()`
- `common/token_usage.py` — token and cost estimates (including cached input rate)

## Reading order

1. `prompt_cache.py` — `STATIC_PROMPTS`, `billable_tokens()`, `PromptCache.resolve()`
2. `app.py` → `main()` — numbered steps 0–8
3. `benchmark.py` — how results are printed

## Setup

From the repo root:

```bash
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY for live runs
```

## Run

```bash
# Token comparison only — no API call, $0
python series-2.2/app.py --dry-run

# Knowledge drift demo — v1/v2/v3 cache sizes, no API
python series-2.2/app.py --drift-demo

# Full benchmark with Gemini (one API call)
python series-2.2/app.py

# Larger static prompts (cache bloat / knowledge drift)
python series-2.2/app.py --cache-version v3 --dry-run
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Token math only; no Gemini call |
| `--drift-demo` | Show v1 → v2 → v3 cache growth and knowledge drift |
| `--cache-version` | Static prompt version: `v1` (lean), `v2` (+security), `v3` (+stale docs) |
| `--question` | Investigation question |
| `--log-file` | HDFS log file path |

## Flow

```
Load HDFS logs
  → prune evidence (series-2.1)
  → build static prompt (cacheable)
  → build dynamic prompt (never cached)
  → Run 1: token accounting without cache
  → Run 2: warm cache → hit → cheaper accounting
  → print benchmark + 100-request projection
```

## Expected output (dry-run, v1)

```
Static tokens:  ~366  |  Dynamic tokens: ~144

WITHOUT PROMPT CACHING  →  ~510 prompt tokens
WITH PROMPT CACHING     →  ~156 prompt tokens (cache HIT)

Input Cost Reduction    →  ~50–80%
100-request projection  →  savings compound at scale
```

## Engineering principles demonstrated

- Cache only **stable** context
- Never cache user questions or runtime logs
- **Version** cached prompts (`v1`, `v2`, `v3`)
- Monitor **cache hit ratio**
- Review caches periodically — **knowledge drift** makes stale prompts dangerous

## Provider neutrality

Cache logic in `prompt_cache.py` is simulated and provider-neutral. The same pattern applies to Gemini context caching, Claude prompt caching, or any LLM with a static system block.

## Previous lab

[Series 2.1 — Context Pruning](../series-2.1/) — shrink evidence **before** caching is applied.
