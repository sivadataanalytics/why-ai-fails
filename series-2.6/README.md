# Series 2.6 — Memory Retrieval

**Engineering Lab:** find the right memory at the right time from a 100,000-record store.

Series 2.5 showed how to **build and compress** long-term memory. Series 2.6 shows how to **retrieve** it intelligently.

## Core principle

> Building memory is only half of the problem.  
> Retrieving the right memory is what makes AI intelligent.

Memory is valuable only when it can be found.

## Retrieval pipeline

```
User Request
    ↓
Intent Detection
    ↓
Memory Search
    ↓
Memory Ranking
    ↓
Top-K Selection
    ↓
Prompt Builder → Gemini
```

## Four strategies

| Strategy | CLI | Approach |
|----------|-----|----------|
| Keyword | `--strategy keyword` | Inverted index, exact term overlap — fast |
| Semantic | `--strategy semantic` | TF-IDF cosine similarity — related concepts |
| Hybrid | `--strategy hybrid` | Keyword + semantic + metadata — enterprise baseline |
| Hybrid + Re-ranking | `--strategy rerank` | Top-20 hybrid → ranking formula → top-K |

## Ranking formula (re-ranking)

```
Memory Score = Semantic Similarity + Confidence + Recency + Business Priority
```

## Files

```
series-2.6/
  app.py           CLI benchmark entry
  memories.py      100k memory generator
  memory_store.py  Inverted index + TF-IDF
  retriever.py     Four retrieval strategies
  ranking.py       Re-ranking + top-K
  evaluator.py     Precision, recall, accuracy
  queries.py       Benchmark queries
  prompts.py       Retrieval prompt template
  benchmark.py     Comparison printer
  Series_2.6_Memory_Retrieval.ipynb  Presentation notebook (slides + live dry-run demo)
  README.md        This file
```

## Dataset

- **100,000** synthetic memory records
- Categories: User Profile, Organization Policies, Project Knowledge, Coding Preferences, Security, Database, Decisions
- Includes duplicates, unrelated noise, obsolete entries (Flask, MySQL), and conflicting preferences

## Run

```bash
# All four strategies — no API key, $0
python series-2.6/app.py --dry-run

# Live Gemini
python series-2.6/app.py

# Single strategy / query
python series-2.6/app.py --strategy rerank --dry-run
python series-2.6/app.py --query-id q3 --top-k 5 --dry-run

# Smaller store for faster dev testing
python series-2.6/app.py --memories 10000 --dry-run
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | No Gemini; retrieval metrics only |
| `--strategy` | `keyword`, `semantic`, `hybrid`, `rerank` |
| `--query-id` | `q1`–`q5` |
| `--top-k` | Memories in prompt (default: 5) |
| `--memories` | Store size (default: 100000) |

## Metrics

| Metric | Description |
|--------|-------------|
| Retrieval Accuracy | Expected values found in top-K |
| Precision | Relevant memories / retrieved |
| Recall | Canonical relevant facts recovered |
| Personalization | Query-specific accuracy |
| Prompt Tokens | Only top-K injected — not 100k |

## Previous labs

- [Series 2.5](../series-2.5/) — Long-Term Memory (build & compress)
- [Series 2.4](../series-2.4/) — Conversation Summarization
- [Series 2.3](../series-2.3/) — RAG Chunking

Series 2.6 completes the memory stack: **store efficiently (2.5), retrieve precisely (2.6).**
