# Series 2.2 — Prompt Caching

Demo: cache **stable** context (system prompt, rules, schema). Never cache **dynamic** context (question, evidence).

## Files

```
app.py           # main demo (~120 lines)
prompt_cache.py  # cache + static prompt versions
benchmark.py     # print results
```

## Run

```bash
python series-2/2.2-prompt-caching/app.py --dry-run
python series-2/2.2-prompt-caching/app.py
python series-2/2.2-prompt-caching/app.py --drift-demo
python series-2/2.2-prompt-caching/app.py --cache-version v3
```

## Flow

1. Load HDFS logs, prune evidence (reuses Series 2.1)
2. Split prompt into **static** (cacheable) + **dynamic** (per request)
3. Compare token accounting: without cache vs with cache hit
