# Series 2 — Prompt Caching (Engineering Lab 2.2)

Demo: cache **stable** context (system prompt, rules, schema). Never cache **dynamic** context (question, evidence).

## Layout

```
series-2/
  app.py           # main demo
  prompt_cache.py  # cache + static prompt versions
  benchmark.py     # print results
```

Reuses `series-1/prune.py` for evidence filtering and `common/` for shared helpers.

## Run

```bash
# From repo root
python series-2/app.py --dry-run
python series-2/app.py
python series-2/app.py --drift-demo
python series-2/app.py --cache-version v3
```

## Flow

1. Load HDFS logs, prune evidence (`series-1/prune.py`)
2. Split prompt into **static** (cacheable) + **dynamic** (per request)
3. Compare token accounting: without cache vs with cache hit
