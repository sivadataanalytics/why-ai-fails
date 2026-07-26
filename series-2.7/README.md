# Series 2.7 — Model Routing

**Engineering Lab:** select the right LLM for each request — not the biggest model every time.

Series 2.6 showed how to **find** the right memory. Series 2.7 shows how to **route** each request to the most cost-effective model tier.

## Core principle

> Enterprise AI systems become efficient by selecting the right model — not the biggest model.

The best AI system knows **when** to use the large model.

## Routing pipeline

```
User Request
    ↓
Intent Detection
    ↓
Task Classification
    ↓
Complexity Estimation
    ↓
Cost Evaluation
    ↓
Security Policy
    ↓
Model Router
    ↓
Best Model → Response
```

## Four strategies

| Strategy | CLI | Approach |
|----------|-----|----------|
| Single Model | `--strategy single` | Everything → large general LLM (baseline) |
| Rule Routing | `--strategy rules` | Static task-type → model map |
| Dynamic Routing | `--strategy dynamic` | Score models on intent, complexity, cost, latency |
| Confidence Routing | `--strategy confidence` | Start cheap; escalate only when needed |

## Model pool

| Model | Best for |
|-------|----------|
| Small Language Model | Translation, classification, summarization |
| Medium Coding Model | SQL, API development, code review |
| Medium Coding (Internal) | Restricted / confidential code |
| Large Reasoning Model | Architecture, legal, complex reasoning |
| Vision Model | Image analysis |
| Large General LLM | Baseline — handles all tasks at highest cost |

## Files

```
series-2.7/
  app.py           CLI benchmark entry
  models.py        Model pool (cost, latency, strengths)
  requests.py      1,000 synthetic AI requests
  classifier.py    Intent detection + task classification
  complexity.py    Simple / medium / complex estimation
  policy.py        Security + budget rules
  router.py        Four routing strategies
  evaluator.py     Accuracy, utilization, escalation rate
  prompts.py       Live Gemini prompt template
  benchmark.py     Comparison printer
  README.md        This file
```

## Run

```bash
# All four strategies — no API key, $0
python series-2.7/app.py --dry-run

# Single strategy
python series-2.7/app.py --strategy confidence --dry-run

# Inspect one request
python series-2.7/app.py --request-id r0025 --dry-run

# Smaller dataset for faster dev
python series-2.7/app.py --requests 100 --dry-run

# Live Gemini (one request)
python series-2.7/app.py --request-id r0025
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Simulated routing metrics; no Gemini |
| `--strategy` | `single`, `rules`, `dynamic`, `confidence` |
| `--request-id` | Inspect/route one request (e.g. `r0025`) |
| `--requests` | Dataset size (default: 1000) |

## Metrics

| Metric | Description |
|--------|-------------|
| Accuracy | Routed model matches expected tier |
| Average Cost | Mean estimated cost per request |
| Latency | Mean simulated latency |
| Model Utilization | % traffic per model |
| Escalation Rate | Confidence routing escalations |

## Previous labs

- [Series 2.6](../series-2.6/) — Memory Retrieval
- [Series 2.5](../series-2.5/) — Long-Term Memory

Series 2.7 completes the cost stack: **prune (2.1), cache (2.2), retrieve (2.3–2.6), route (2.7).**
