# Series 2.4 — Conversation Summarization

**Engineering Lab:** reduce prompt size while preserving conversational memory.

Conversations grow forever. Memory shouldn't. This lab benchmarks four summarization strategies on a **175-message** enterprise AI coding assistant conversation.

## What this demo proves

| Strategy | Approach | Tradeoff |
|----------|----------|----------|
| **Full** | Send entire history | Perfect memory, highest cost |
| **Rolling** | Summary + latest 10 messages | Good memory, much lower cost |
| **Hierarchical** | 20-msg blocks → master summary + latest 10 | Scales to long threads |
| **Semantic** | Structured facts only + latest 5 | Highest information density |

## Core principle

> Conversation summarization is **memory management** — not simply token optimization.

The objective is not to remember every message. The objective is to remember the **right information**.

## Architecture

**Without summarization:**
```
175 Messages → Prompt Builder → Gemini
```

**With summarization:**
```
175 Messages → Summarizer → Conversation Memory + Latest Messages → Prompt Builder → Gemini
```

Gemini never receives the full conversation (except in the `full` baseline strategy).

## Files

```
series-2.4/
  app.py                   CLI entry — load conversation, run benchmark
  conversation_dataset.py  ~175 synthetic messages + benchmark questions
  conversation_loader.py   Load conversation into memory
  summarizer.py            Four summarization strategies
  memory.py                Structured semantic memory extraction
  evaluator.py             Memory Score + context retention
  prompts.py               Prompt templates for Gemini
  benchmark.py             Side-by-side comparison printer
  README.md                This file
```

## Benchmark metrics

| Metric | Description |
|--------|-------------|
| Prompt Tokens | Input size sent to Gemini |
| Completion Tokens | Model output |
| Latency | Wall-clock time (estimated in dry-run) |
| Estimated Cost | From `common/token_usage.py` |
| Summary Size | Token count of compressed memory |
| Memory Score | Remembered facts / expected facts |
| Context Retention | Memory score relative to full conversation |

## Expected memory facts

The conversation embeds facts summarization should preserve:

- Python (language preference)
- Prompt Caching (earlier project)
- Conversation Summarization (current project)
- Rolling / Hierarchical / Semantic Summary (strategies)
- Pending benchmark tasks
- Architecture decisions (static prompt split, versioning)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # optional for live runs
```

## Run

```bash
# Compare all four strategies — no API, $0
python series-2.4/app.py --dry-run

# Live run (4 Gemini calls — one per strategy)
python series-2.4/app.py

# Single strategy
python series-2.4/app.py --strategy semantic --dry-run

# Different benchmark question
python series-2.4/app.py --question-id q3 --dry-run
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Token estimates + memory scores only |
| `--strategy` | `full`, `rolling`, `hierarchical`, `semantic` |
| `--question-id` | `q1`–`q5` (default: `q5`) |

## Benchmark questions

| ID | Question |
|----|----------|
| q1 | What programming language does the user prefer? |
| q2 | What project is the user currently working on? |
| q3 | What architectural decisions have already been made? |
| q4 | What task is still pending? |
| q5 | Summarize the current engineering objective. |

## Design choices

- **No LangChain / LlamaIndex** — plain Python, readable for students
- **Local summarizers** — deterministic compression for reproducible dry-runs
- **Reuses `common/`** — `gemini_client`, `token_usage`, `config`

## Previous labs

- [Series 2.1](../series-2.1/) — Context Pruning
- [Series 2.2](../series-2.2/) — Prompt Caching
- [Series 2.3](../series-2.3/) — RAG Chunking

Series 2.4 adds the **conversation memory** layer: after you prune, cache, and chunk, long chat sessions still need summarization to stay within cost and latency limits.
