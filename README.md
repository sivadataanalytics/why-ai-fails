# Why AI Fails? — Engineering Lab (Series 2)

Hands-on demos showing **why AI systems fail in production** — and the engineering patterns that fix them.

This repo focuses on **token economics**: what you send to the LLM, what you pay for, and how to optimize without sacrificing answer quality.

## Labs

| Folder | Topic | Notebook | Core idea |
|--------|-------|----------|-----------|
| [series-2.1/](series-2.1/) | Context Pruning | [Series_2.1_Context_Pruning.ipynb](series-2.1/Series_2.1_Context_Pruning.ipynb) | Send **less** evidence — filter logs before the prompt |
| [series-2.2/](series-2.2/) | Prompt Caching | [Series_2.2_Prompt_Caching.ipynb](series-2.2/Series_2.2_Prompt_Caching.ipynb) | Don't **re-process** the same stable system prompt every request |
| [series-2.3/](series-2.3/) | RAG Chunking | [Series_2.3_RAG_Chunking.ipynb](series-2.3/Series_2.3_RAG_Chunking.ipynb) | Retrieve the **right** evidence — benchmark chunk size, don't guess |
| [series-2.4/](series-2.4/) | Conversation Summarization | [Series_2.4_Conversation_Summarization.ipynb](series-2.4/Series_2.4_Conversation_Summarization.ipynb) | **Memory** management — summarize history, preserve facts, cut prompt size |
| [series-2.5/](series-2.5/) | Long-Term Memory | [Series_2.5_Long_Term_Memory.ipynb](series-2.5/Series_2.5_Long_Term_Memory.ipynb) | **Compress** knowledge across 500 conversations; retrieve only what matters |
| [series-2.6/](series-2.6/) | Memory Retrieval | [Series_2.6_Memory_Retrieval.ipynb](series-2.6/Series_2.6_Memory_Retrieval.ipynb) | **Find** the right memory from 100k records — keyword, semantic, hybrid, re-rank |
| [series-2.7/](series-2.7/) | Model Routing | [Series_2.7_Model_Routing.ipynb](series-2.7/Series_2.7_Model_Routing.ipynb) | **Select** the right LLM per request — cost, latency, and accuracy |
| [series-2.8/](series-2.8/) | Multi-Agent Orchestration | [Series_2.8_Multi_Agent_Orchestration.ipynb](series-2.8/Series_2.8_Multi_Agent_Orchestration.ipynb) | **Coordinate** specialized agents — single vs sequential vs parallel vs reviewer |

Series 2.2 builds on 2.1: evidence is still pruned; caching applies only to the static system prompt.  
Series 2.3 adds the retrieval layer: same corpus and questions, different chunking strategies.  
Series 2.4 adds conversation memory: long chat sessions need summarization, not full history in every prompt.  
Series 2.5 adds persistent user memory: extract, compress, and retrieve durable facts across hundreds of conversations.  
Series 2.6 scales retrieval: 100k memory store with hybrid search and re-ranking for enterprise personalization.  
Series 2.7 adds model routing: send simple requests to small models, escalate only when confidence is low.  
Series 2.8 adds multi-agent orchestration: coordinate specialized agents through shared memory — quality per unit time, not agent count alone.

## Quick start

**Full one-time setup:** see [SETUP.md](SETUP.md) (clone, venv, dependencies, verify all labs, notebooks, troubleshooting).

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

# Series 2.6 — Memory Retrieval ($0 dry-run)
python series-2.6/app.py --dry-run

# Series 2.7 — Model Routing ($0 dry-run)
python series-2.7/app.py --dry-run

# Series 2.8 — Multi-Agent Orchestration ($0 dry-run)
python series-2.8/app.py --dry-run
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
series-2.6/       Memory retrieval benchmark (100k store)
series-2.7/       Model routing benchmark (1k requests)
series-2.8/       Multi-agent orchestration benchmark (500 requests)
demo.py           Entry point for Series 2.1
```

## Datasets

- **Series 2.1 / 2.2:** `datasets/HDFS_2k.log` — 2,000 HDFS log lines from LogHub. Default question targets block `blk_-8775602795571523802`.
- **Series 2.3:** `docs/` — Why AI Fails article corpus (economics, pruning, caching, chunking).
- **Series 2.4:** `series-2.4/conversation_dataset.py` — synthetic ~175-message enterprise AI assistant conversation.
- **Series 2.5:** `series-2.5/conversations.py` — 500 simulated conversations for one enterprise user.
- **Series 2.6:** `series-2.6/memories.py` — 100,000 synthetic long-term memory records.
- **Series 2.7:** `series-2.7/requests.py` — 1,000 synthetic AI requests across 10 task categories.
- **Series 2.8:** `series-2.8/tasks.py` — 500 enterprise software build requests across 8 categories.
