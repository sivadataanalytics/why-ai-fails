# Series 2.3 — RAG Chunking Benchmark

**Engineering Lab:** find the right chunk size with benchmarks, not assumptions.

Most RAG applications eventually ask: *What is the right chunk size?* This lab answers that by testing the **same documents, same questions, and same model** across different chunking strategies — changing only how documents are split.

## What this demo proves

| Factor | Why it matters |
|--------|----------------|
| Retrieval quality | Hit Score — did retrieved chunks contain expected terms? |
| Prompt tokens | Larger chunks → more text in the prompt |
| Latency | More prompt tokens → slower responses |
| Estimated cost | Token usage drives the bill |
| Answer quality | Right evidence beats more evidence |

## Core principle

> Chunk according to how users ask questions — not framework defaults.

Better RAG is not about retrieving more context. Better RAG is about retrieving the **right evidence** with the **lowest useful cost**.

## High-level flow

```
Documents (docs/)
    ↓
Chunking Strategy (small / medium / large)
    ↓
Keyword Retriever (top-k)
    ↓
Prompt Builder
    ↓
Gemini (or --dry-run)
    ↓
Benchmark (hit score + tokens + cost)
```

## Files

```
series-2.3/
  app.py            CLI entry — load docs, run strategies, call Gemini
  chunker.py        Fixed-size and semantic chunking
  retriever.py      Keyword scoring + hit score
  questions.py      Benchmark questions + expected terms
  prompt_builder.py RAG prompt template
  benchmark.py      Side-by-side comparison printer
  README.md         This file
```

**Corpus (repo root):**

```
docs/
  series_2_hidden_economics.txt
  series_2_1_context_pruning.txt
  series_2_2_prompt_caching.txt
  series_2_3_rag_chunking.txt
```

## Chunking strategies

| Strategy | Chunk size | Overlap | Expected behavior |
|----------|------------|---------|-------------------|
| `small` | 200 tokens | 0 | Lower cost, may miss cross-section context |
| `medium` | 500 tokens | 50 | Balanced retrieval and cost |
| `large` | 1000 tokens | 100 | More context per chunk, higher prompt cost |
| `semantic` | by `#` headings | — | Structure-aware sections (optional) |

## Hit Score

Simple retrieval quality metric per question:

```
Hit Score = matched expected terms / total expected terms
```

Example: 3 of 4 expected terms found → Hit Score = 0.75

## Setup

From the repo root:

```bash
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY for live runs
```

## Run

```bash
# Compare all three strategies on all questions — no API, $0
python series-2.3/app.py --dry-run

# Live run with Gemini (one call per strategy per question)
python series-2.3/app.py

# Single question
python series-2.3/app.py --question-id q1 --dry-run

# Single strategy
python series-2.3/app.py --strategy medium --dry-run

# Retrieve more chunks
python series-2.3/app.py --top-k 5 --dry-run

# Semantic chunking (heading-based)
python series-2.3/app.py --strategy semantic --dry-run
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Token estimates and hit scores only; no Gemini |
| `--question-id` | Run one question: `q1`, `q2`, or `q3` |
| `--strategy` | Run one strategy: `small`, `medium`, `large`, `semantic` |
| `--top-k` | Number of chunks to retrieve (default: 3) |
| `--docs-dir` | Path to corpus folder (default: `docs/`) |

## Benchmark questions

| ID | Question |
|----|----------|
| q1 | How is Prompt Caching different from Context Pruning? |
| q2 | Why does chunk size affect RAG cost? |
| q3 | What is Knowledge Drift in prompt caches? |

## Expected observations

- **Small chunks** often reduce prompt tokens but may score lower on comparison questions that span multiple sections.
- **Large chunks** may hit all expected terms but at higher prompt cost and latency.
- **Medium chunks** frequently offer the best balance for documentation-style corpora.
- The **cheapest** strategy is not always the best; the **largest** chunks are not always best.

## Design choices (intentionally simple)

- **No vector database** — keyword retriever so the logic is readable
- **No LangChain** — plain Python matching Series 2.1 / 2.2 style
- **Provider-neutral pricing** — uses `common/token_usage.py` placeholders

## Previous labs

- [Series 2.1 — Context Pruning](../series-2.1/) — filter evidence before the prompt
- [Series 2.2 — Prompt Caching](../series-2.2/) — cache stable system prompts

Series 2.3 completes the retrieval layer: after you prune and cache, you still need to **chunk and retrieve** the right knowledge.
