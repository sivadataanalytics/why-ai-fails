# Why AI Fails? — Engineering Lab (Series 2)

Hands-on demos showing **why AI systems fail in production** — and the engineering patterns that fix them.

This repo focuses on **token economics**: what you send to the LLM, what you pay for, and how to optimize without sacrificing answer quality.

## Labs

| Folder | Topic | Core idea |
|--------|-------|-----------|
| [series-2.1/](series-2.1/) | Context Pruning | Send **less** evidence — filter logs before the prompt |
| [series-2.2/](series-2.2/) | Prompt Caching | Don't **re-process** the same stable system prompt every request |
| [series-2.3/](series-2.3/) | RAG Chunking | Retrieve the **right** evidence — benchmark chunk size, don't guess |
| [series-2.4/](series-2.4/) | Conversation Summarization | **Memory** management — summarize history, preserve facts, cut prompt size |
| [series-2.5/](series-2.5/) | Long-Term Memory | **Compress** knowledge across 500 conversations; retrieve only what matters |

Series 2.2 builds on 2.1: evidence is still pruned; caching applies only to the static system prompt.  
Series 2.3 adds the retrieval layer: same corpus and questions, different chunking strategies.  
Series 2.4 adds conversation memory: long chat sessions need summarization, not full history in every prompt.  
Series 2.5 adds persistent user memory: extract, compress, and retrieve durable facts across hundreds of conversations.

## Quick start

```bash
# Setup (once)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY for live runs

# Series 2.1 — Context Pruning ($0 dry-run)
python demo.py --dry-run

# Series 2.2 — Prompt Caching ($0 dry-run)
python series-2.2/app.py --dry-run

# Series 2.3 — RAG Chunking ($0 dry-run)
python series-2.3/app.py --dry-run

# Series 2.4 — Conversation Summarization ($0 dry-run)
python series-2.4/app.py --dry-run

# Series 2.5 — Long-Term Memory ($0 dry-run)
python series-2.5/app.py --dry-run
```

## Repository layout

```
common/           Shared config, Gemini client, prompt builders, token math
datasets/         HDFS_2k.log (LogHub sample, used by Series 2.1 / 2.2)
docs/             Article corpus for Series 2.3 RAG chunking benchmark
series-2.1/       Context pruning demo
series-2.2/       Prompt caching demo
series-2.3/       RAG chunking benchmark
series-2.4/       Conversation summarization benchmark
series-2.5/       Long-term memory compression benchmark
demo.py           Entry point for Series 2.1
```

## Datasets

- **Series 2.1 / 2.2:** `datasets/HDFS_2k.log` — 2,000 HDFS log lines from LogHub. Default question targets block `blk_-8775602795571523802`.
- **Series 2.3:** `docs/` — Why AI Fails article corpus (economics, pruning, caching, chunking).
- **Series 2.4:** `series-2.4/conversation_dataset.py` — synthetic ~175-message enterprise AI assistant conversation.
- **Series 2.5:** `series-2.5/conversations.py` — 500 simulated conversations for one enterprise user.
