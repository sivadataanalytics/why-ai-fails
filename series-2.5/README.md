# Series 2.5 — Long-Term AI Memory

**Engineering Lab:** maintain long-term user memory without unbounded growth.

500 simulated conversations → extract durable knowledge → compress duplicates → retrieve only relevant memories for the prompt.

## Core principle

> Long-term memory is not a conversation archive.  
> It is a compressed knowledge base.

Conversation history grows forever. Long-term memory shouldn't.

## What this demo proves

| Strategy | What it does |
|----------|--------------|
| **No compression** | Store every extracted memory — largest store and prompt |
| **Deduplication** | Same category+key → single memory |
| **Full compression** | Dedup + consolidate + update + expire |
| **Compression + retrieval** | Compressed store + top-K relevant memories only in prompt |

## Architecture

```
500 Conversations
    ↓
Memory Extractor
    ↓
Memory Compressor
    ↓
Memory Store (JSON profile)
    ↓
Memory Retriever (top-K)
    ↓
Prompt Builder → Gemini
```

## Compression operations

1. **Deduplication** — duplicate memories → single memory  
2. **Consolidation** — FastAPI + Pydantic + SQLAlchemy → Python Backend Stack  
3. **Updating** — PyCharm → VS Code (latest wins, no duplicate)  
4. **Expiration** — drop temporary / low-confidence / obsolete entries  

## Files

```
series-2.5/
  app.py                 CLI entry — run benchmark
  conversations.py       500 simulated conversations + benchmark questions
  conversation_loader.py Load conversations
  memory_extractor.py    Extract structured memories
  memory_compressor.py   Dedup, consolidate, update, expire
  memory_store.py        JSON profile storage
  memory_retriever.py    Intent + keyword top-K retrieval
  evaluator.py           Retrieval accuracy metrics
  prompts.py             Prompt template with memory injection
  benchmark.py           Comparison printer
  README.md              This file
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # optional for live runs
```

## Run

```bash
# All four strategies — no API, $0
python series-2.5/app.py --dry-run

# Live run
python series-2.5/app.py

# Single strategy
python series-2.5/app.py --strategy retrieval --dry-run

# Different question
python series-2.5/app.py --question-id q3 --dry-run

# Fewer conversations (faster dev test)
python series-2.5/app.py --conversations 100 --dry-run
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | No Gemini; token estimates + retrieval accuracy only |
| `--strategy` | `raw`, `dedup`, `compressed`, `retrieval` |
| `--question-id` | `q1`–`q5` (default: `q1`) |
| `--conversations` | Number of conversations to simulate (default: 500) |
| `--top-k` | Memories retrieved for prompt (default: 5) |

## Benchmark questions

| ID | Question |
|----|----------|
| q1 | Generate a secure FastAPI REST API. |
| q2 | Generate Python code. |
| q3 | What framework does the user prefer? |
| q4 | Which database should be used? |
| q5 | Generate code following organization standards. |

## Metrics

| Metric | Description |
|--------|-------------|
| Memory Size | Estimated tokens in compressed store |
| Prompt Tokens | Input sent to Gemini |
| Retrieval Accuracy | Expected memories found / total expected |
| Personalization | Question-specific memory match |
| Latency / Cost | From `common/token_usage.py` |

## Expected memories (global)

Python, FastAPI, Secure Coding, PostgreSQL, Readable Python

## Previous labs

- [Series 2.4](../series-2.4/) — Conversation Summarization (session memory)
- [Series 2.3](../series-2.3/) — RAG Chunking
- [Series 2.2](../series-2.2/) — Prompt Caching
- [Series 2.1](../series-2.1/) — Context Pruning

Series 2.5 adds **persistent user memory** across many conversations — the layer above session summarization.
