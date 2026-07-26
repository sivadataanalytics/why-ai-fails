#!/usr/bin/env python3
"""Generate presentation notebooks for series 2.3–2.7 (same format as 2.1)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEMO_CELL = """# Live demo cell — run the dry-run benchmark ($0, no API key needed)
# Execute this cell during your presentation

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "demo.py").exists() and (ROOT.parent / "demo.py").exists():
    ROOT = ROOT.parent

result = subprocess.run(
    [sys.executable, str(ROOT / "{app_path}"), "--dry-run"],
    cwd=str(ROOT),
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
print(f"\\nExit code: {result.returncode}")
"""

NOTEBOOKS: list[dict] = [
    {
        "path": ROOT / "series-2.3/Series_2.3_RAG_Chunking.ipynb",
        "app_path": "series-2.3/app.py",
        "cells": [
            (
                "# Series 2.3 — RAG Chunking\n\n"
                "**Why AI Fails? — Engineering Lab**\n\n"
                "---\n\n"
                "> Most RAG apps ask: *What is the right chunk size?*  \n"
                "> This lab answers with **benchmarks**, not framework defaults.\n\n"
                "**Scenario:** Same documentation corpus, same questions, same model — "
                "only **how documents are split** changes.\n\n"
                "**Core lesson:** Better RAG is not retrieving **more** context. "
                "It is retrieving the **right evidence** at the **lowest useful cost**."
            ),
            (
                "## 1. The Problem\n\n"
                "| Bad RAG assumption | Engineering approach |\n"
                "|--------------------|----------------------|\n"
                "| \"Use 512 tokens because the tutorial said so\" | Benchmark small / medium / large / semantic on **your** corpus |\n"
                "| Retrieve more chunks = better answers | Hit Score + prompt tokens show the tradeoff |\n"
                "| One chunk size fits all questions | Chunk according to **how users ask** |\n"
                "| Ignore cost until the bill arrives | Measure tokens, latency, and estimated cost per strategy |\n\n"
                "### Why this matters in production\n\n"
                "- Wrong chunk size → **missed evidence** (too small) or **bloated prompts** (too large)\n"
                "- Every extra token in retrieved chunks is billed **on every question**\n"
                "- Retrieval quality and cost move together — you must measure both\n\n"
                "**Expected dry-run insight:**\n\n"
                "```\n"
                "SMALL   → lower prompt tokens, may miss cross-section context\n"
                "MEDIUM  → often best balance for documentation-style corpora\n"
                "LARGE   → higher hit scores sometimes, higher prompt cost always\n"
                "SEMANTIC→ structure-aware sections when docs have clear headings\n"
                "```"
            ),
            (
                "## 2. What is RAG Chunking?\n\n"
                "**RAG chunking** is how you **split source documents** into retrievable pieces "
                "before embedding or keyword search.\n\n"
                "It is not about changing the LLM, the retriever algorithm, or the user question. "
                "It is about **defining the unit of evidence** the model reads.\n\n"
                "### Definition\n\n"
                "```\n"
                "RAG chunking = documents → chunks → retrieve top-K → prompt → LLM\n"
                "               (chunk size is the first cost/quality lever)\n"
                "```\n\n"
                "### Chunk size tradeoffs\n\n"
                "| Smaller chunks | Larger chunks |\n"
                "|----------------|---------------|\n"
                "| Lower prompt cost per retrieval | More context per chunk |\n"
                "| Precise keyword hits | May include irrelevant padding |\n"
                "| May split related facts across chunks | Higher token bill |\n"
                "| Good for fact lookup | Good for narrative / comparison questions |\n\n"
                "### What RAG chunking is NOT\n\n"
                "| Technique | Difference |\n"
                "|-----------|------------|\n"
                "| **Context pruning** (Series 2.1) | Pruning filters **one request's** evidence; chunking defines **document structure** |\n"
                "| **Prompt caching** (Series 2.2) | Caching reuses stable instructions; chunks are **changing retrieved content** |\n"
                "| **Embedding model choice** | Chunking happens **before** vectors are created |\n"
                "| **Top-K tuning** | Top-K chooses **how many** chunks; chunking defines **what each chunk contains** |\n\n"
                "### This lab's implementation\n\n"
                "```\n"
                "docs/ corpus\n"
                "    → chunker.py (small / medium / large / semantic)\n"
                "    → retriever.py (keyword + Hit Score)\n"
                "    → prompt_builder.py → Gemini\n"
                "```\n\n"
                "> **Enterprise principle:** Benchmark chunk strategies on real questions — "
                "don't copy framework defaults."
            ),
            (
                "## 3. Repository Layout\n\n"
                "```\n"
                "why-ai-fails/\n"
                "├── docs/                          ← Article corpus for RAG benchmark\n"
                "│   ├── series_2_hidden_economics.txt\n"
                "│   ├── series_2_1_context_pruning.txt\n"
                "│   ├── series_2_2_prompt_caching.txt\n"
                "│   └── series_2_3_rag_chunking.txt\n"
                "├── common/                        ← Shared Gemini client, token math\n"
                "└── series-2.3/\n"
                "    ├── app.py                     ← CLI + benchmark runner\n"
                "    ├── chunker.py                 ← Fixed-size + semantic chunking\n"
                "    ├── retriever.py               ← Keyword scoring + Hit Score\n"
                "    ├── questions.py               ← Benchmark Q&A + expected terms\n"
                "    ├── prompt_builder.py          ← RAG prompt template\n"
                "    ├── benchmark.py               ← Side-by-side comparison\n"
                "    ├── README.md\n"
                "    └── Series_2.3_RAG_Chunking.ipynb   ← This notebook\n"
                "```"
            ),
            (
                "## 4. The Chunking Pipeline (`chunker.py`)\n\n"
                "```\n"
                "docs/*.txt\n"
                "    │\n"
                "    ▼  Strategy: small (200 tokens, 0 overlap)\n"
                "    ▼  Strategy: medium (500 tokens, 50 overlap)\n"
                "    ▼  Strategy: large (1000 tokens, 100 overlap)\n"
                "    ▼  Strategy: semantic (split on # headings)\n"
                "    │\n"
                "    ▼  retriever.py → top-K chunks + Hit Score\n"
                "    ▼  prompt_builder.py → Gemini (or --dry-run)\n"
                "```\n\n"
                "| Strategy | Chunk size | Overlap | Expected behavior |\n"
                "|----------|------------|---------|-------------------|\n"
                "| `small` | 200 tokens | 0 | Lower cost, may miss cross-section context |\n"
                "| `medium` | 500 tokens | 50 | Balanced retrieval and cost |\n"
                "| `large` | 1000 tokens | 100 | More context per chunk, higher prompt cost |\n"
                "| `semantic` | by `#` headings | — | Structure-aware sections |\n\n"
                "**Hit Score** = matched expected terms / total expected terms (retrieval quality proxy)."
            ),
            (
                "## 5. Three Layers of RAG Engineering\n\n"
                "### Layer 1 — Same corpus, same questions (controlled experiment)\n\n"
                "Every strategy runs on **identical** documents and benchmark questions. "
                "Only chunking changes — so differences in Hit Score and tokens are attributable.\n\n"
                "---\n\n"
                "### Layer 2 — Retrieve the right evidence (not all evidence)\n\n"
                "Keyword retriever scores chunks, selects top-K, and builds a prompt with **only** those chunks.\n\n"
                "```\n"
                "Question → tokenize → score all chunks → top-K → prompt\n"
                "```\n\n"
                "The anti-pattern: dump entire documents into every prompt \"just in case.\"\n\n"
                "---\n\n"
                "### Layer 3 — Measure (Hit Score + tokens + cost)\n\n"
                "| Metric | What it tells you |\n"
                "|--------|-------------------|\n"
                "| **Hit Score** | Did retrieved chunks contain expected terms? |\n"
                "| **Prompt tokens** | Cost driver — scales with chunk size × top-K |\n"
                "| **Latency / Cost** | From `common/token_usage.py` |\n\n"
                "| Mode | Flag | API key? |\n"
                "|------|------|----------|\n"
                "| **Dry-run** | `--dry-run` | No — Hit Score + token estimates, **$0** |\n"
                "| **Live** | (none) | Yes — real Gemini answers per strategy |"
            ),
            (
                "## 6. Execution Flow\n\n"
                "```\n"
                "Parse CLI args (--strategy, --question-id, --top-k)\n"
                "    │\n"
                "    └─ Load docs/ corpus\n"
                "            │\n"
                "            For each chunking strategy:\n"
                "                chunk documents\n"
                "                retrieve top-K for each benchmark question\n"
                "                compute Hit Score + token estimate\n"
                "                → Gemini (unless --dry-run)\n"
                "            │\n"
                "            └─ print_benchmark() — side-by-side comparison\n"
                "```"
            ),
            (
                "## 7. How to Run\n\n"
                "From the **repo root**:\n\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "cp .env.example .env   # optional — only for live Gemini calls\n"
                "```\n\n"
                "| Command | What it does | API key? |\n"
                "|---------|--------------|----------|\n"
                "| `python series-2.3/app.py --dry-run` | All strategies, all questions | No |\n"
                "| `python series-2.3/app.py --strategy medium --dry-run` | Single strategy | No |\n"
                "| `python series-2.3/app.py --question-id q1 --dry-run` | Single question | No |\n"
                "| `python series-2.3/app.py` | Live Gemini benchmark | Yes |"
            ),
            (
                "## 8. Key Code Snippets\n\n"
                "### Chunk strategies (`chunker.py`)\n\n"
                "```python\n"
                "STRATEGIES = {\n"
                "    \"small\":  {\"chunk_size\": 200,  \"overlap\": 0,   \"mode\": \"fixed\"},\n"
                "    \"medium\": {\"chunk_size\": 500,  \"overlap\": 50,  \"mode\": \"fixed\"},\n"
                "    \"large\":  {\"chunk_size\": 1000, \"overlap\": 100, \"mode\": \"fixed\"},\n"
                "    \"semantic\": {\"mode\": \"semantic\"},  # split on # headings\n"
                "}\n"
                "```\n\n"
                "### Hit Score (`retriever.py`)\n\n"
                "```python\n"
                "def compute_hit_score(retrieved_text: str, expected_terms: list[str]) -> float:\n"
                "    matched = sum(1 for t in expected_terms if t.lower() in retrieved_text.lower())\n"
                "    return matched / len(expected_terms)\n"
                "```"
            ),
            (
                "## 9. Where Series 2.3 Fits\n\n"
                "| Lab | Topic | Builds on prior labs by… |\n"
                "|-----|-------|--------------------------|\n"
                "| 2.1 | Context Pruning | Shrinks evidence before the prompt |\n"
                "| 2.2 | Prompt Caching | Reuses stable system instructions |\n"
                "| **2.3** | **RAG Chunking** | Defines **how knowledge is split** for retrieval |\n"
                "| 2.4 | Conversation Summarization | Compresses chat history |\n"
                "| 2.5 | Long-Term Memory | Stores durable user facts |\n"
                "| 2.6 | Memory Retrieval | Finds the right memory at scale |\n"
                "| 2.7 | Model Routing | Selects the right model per request |\n\n"
                "---\n\n"
                "## Takeaway\n\n"
                "> **Chunk according to how users ask questions — not framework defaults.**\n\n"
                "**Next lab:** [Series 2.4 — Conversation Summarization](../series-2.4/) — "
                "long chat sessions need memory management, not full history replay."
            ),
        ],
    },
    {
        "path": ROOT / "series-2.4/Series_2.4_Conversation_Summarization.ipynb",
        "app_path": "series-2.4/app.py",
        "cells": [
            (
                "# Series 2.4 — Conversation Summarization\n\n"
                "**Why AI Fails? — Engineering Lab**\n\n"
                "---\n\n"
                "> Conversations grow forever. Memory shouldn't.\n\n"
                "**Scenario:** A 175-message enterprise AI coding assistant thread — "
                "four summarization strategies, one benchmark question.\n\n"
                "**Core lesson:** Conversation summarization is **memory management** — "
                "remember the **right information**, not every message."
            ),
            (
                "## 1. The Problem\n\n"
                "| Without summarization | With summarization |\n"
                "|-----------------------|--------------------|\n"
                "| All 175 messages in every prompt | Summary + recent messages only |\n"
                "| Prompt size grows linearly with chat length | Prompt size stays bounded |\n"
                "| High cost, high latency | Much lower cost, faster responses |\n"
                "| Model sees noise (greetings, thanks) | Model sees facts and decisions |\n\n"
                "### Why this matters in production\n\n"
                "- Support bots and coding assistants accumulate **unbounded history**\n"
                "- Replaying full transcripts on every turn wastes tokens on irrelevant chatter\n"
                "- The model needs **decisions, preferences, and pending tasks** — not \"good morning\"\n\n"
                "**Expected dry-run insight:**\n\n"
                "```\n"
                "FULL          → highest Memory Score, highest prompt tokens\n"
                "ROLLING       → good memory, much lower cost\n"
                "HIERARCHICAL  → scales to very long threads\n"
                "SEMANTIC      → highest information density per token\n"
                "```"
            ),
            (
                "## 2. What is Conversation Summarization?\n\n"
                "**Conversation summarization** compresses chat history into a **compact memory representation** "
                "while preserving facts the assistant must remember across turns.\n\n"
                "It is not about shortening the user's latest question. It is about **not replaying "
                "the entire conversation** on every API call.\n\n"
                "### Definition\n\n"
                "```\n"
                "Conversation summarization = full history → memory + recent window → prompt → LLM\n"
                "                               (runs BEFORE each new turn)\n"
                "```\n\n"
                "### Four strategies in this lab\n\n"
                "| Strategy | What enters the prompt |\n"
                "|----------|------------------------|\n"
                "| **Full** | Entire 175-message history (baseline) |\n"
                "| **Rolling** | Evolving summary + latest 10 messages |\n"
                "| **Hierarchical** | Block summaries → master summary + latest 10 |\n"
                "| **Semantic** | Structured facts only + latest 5 messages |\n\n"
                "### What summarization is NOT\n\n"
                "| Technique | Difference |\n"
                "|-----------|------------|\n"
                "| **Context pruning** (Series 2.1) | Pruning filters external evidence (logs); summarization compresses **chat** |\n"
                "| **Long-term memory** (Series 2.5) | Summarization is **session-scoped**; long-term memory persists **across sessions** |\n"
                "| **RAG chunking** (Series 2.3) | RAG chunks **documents**; summarization chunks **conversation turns** |\n\n"
                "> **Enterprise principle:** Summarize deterministically where possible — "
                "reproducible dry-runs, testable memory scores."
            ),
            (
                "## 3. Repository Layout\n\n"
                "```\n"
                "why-ai-fails/\n"
                "├── common/                        ← Gemini client, token math\n"
                "└── series-2.4/\n"
                "    ├── app.py                     ← CLI + benchmark runner\n"
                "    ├── conversation_dataset.py    ← ~175 synthetic messages\n"
                "    ├── conversation_loader.py     ← Load conversation into memory\n"
                "    ├── summarizer.py              ← Four summarization strategies\n"
                "    ├── memory.py                  ← Structured semantic memory\n"
                "    ├── evaluator.py               ← Memory Score + retention\n"
                "    ├── prompts.py                 ← Prompt templates\n"
                "    ├── benchmark.py               ← Side-by-side comparison\n"
                "    ├── README.md\n"
                "    └── Series_2.4_Conversation_Summarization.ipynb   ← This notebook\n"
                "```"
            ),
            (
                "## 4. The Summarization Pipeline (`summarizer.py`)\n\n"
                "**Without summarization:**\n"
                "```\n"
                "175 Messages → Prompt Builder → Gemini\n"
                "```\n\n"
                "**With summarization:**\n"
                "```\n"
                "175 Messages → Summarizer → Memory + Latest Messages → Prompt → Gemini\n"
                "```\n\n"
                "| Strategy | Window | Compression method |\n"
                "|----------|--------|--------------------|\n"
                "| Rolling | Latest 10 verbatim | Bullet summary of older messages |\n"
                "| Hierarchical | Latest 10 verbatim | 20-msg blocks → master summary |\n"
                "| Semantic | Latest 5 verbatim | Extract structured facts; drop noise |\n\n"
                "Summaries are built **locally** (no LLM) so `--dry-run` works without an API key."
            ),
            (
                "## 5. Three Layers of Conversation Memory\n\n"
                "### Layer 1 — Preserve what matters (Memory Score)\n\n"
                "Benchmark questions test whether summarization retained:\n"
                "- Python preference, project name, architectural decisions, pending tasks\n\n"
                "**Memory Score** = remembered facts / expected facts\n\n"
                "---\n\n"
                "### Layer 2 — Compress before the prompt\n\n"
                "Filter noise phrases (`thank you`, `good morning`, …) from summaries. "
                "Semantic strategy keeps **structured facts** only.\n\n"
                "---\n\n"
                "### Layer 3 — Measure tokens vs memory\n\n"
                "| Metric | What it tells you |\n"
                "|--------|-------------------|\n"
                "| **Prompt tokens** | Cost of replaying history |\n"
                "| **Summary size** | Compressed memory footprint |\n"
                "| **Memory Score** | Did we lose critical facts? |\n"
                "| **Context retention** | Score relative to full conversation |\n\n"
                "| Mode | Flag | API key? |\n"
                "|------|------|----------|\n"
                "| **Dry-run** | `--dry-run` | No — **$0** |\n"
                "| **Live** | (none) | Yes — 4 Gemini calls (one per strategy) |"
            ),
            (
                "## 6. Execution Flow\n\n"
                "```\n"
                "Parse CLI args (--strategy, --question-id)\n"
                "    │\n"
                "    └─ Load 175-message conversation\n"
                "            │\n"
                "            For each strategy (full / rolling / hierarchical / semantic):\n"
                "                build_summary() → memory + recent messages\n"
                "                build_prompt() → token estimate or Gemini\n"
                "                compute Memory Score\n"
                "            │\n"
                "            └─ print_benchmark()\n"
                "```"
            ),
            (
                "## 7. How to Run\n\n"
                "From the **repo root**:\n\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "cp .env.example .env   # optional\n"
                "```\n\n"
                "| Command | What it does | API key? |\n"
                "|---------|--------------|----------|\n"
                "| `python series-2.4/app.py --dry-run` | All four strategies | No |\n"
                "| `python series-2.4/app.py --strategy semantic --dry-run` | Single strategy | No |\n"
                "| `python series-2.4/app.py --question-id q5 --dry-run` | Different question | No |\n"
                "| `python series-2.4/app.py` | Live Gemini | Yes |"
            ),
            (
                "## 8. Key Code Snippets\n\n"
                "### Strategy windows (`summarizer.py`)\n\n"
                "```python\n"
                "LATEST_ROLLING = 10\n"
                "LATEST_HIERARCHICAL = 10\n"
                "LATEST_SEMANTIC = 5\n"
                "HIERARCHICAL_BLOCK = 20\n"
                "```\n\n"
                "### Noise filtering\n\n"
                "```python\n"
                "NOISE_PHRASES = (\"thank you\", \"thanks\", \"good morning\", \"got it\", ...)\n"
                "\n"
                "def _is_low_value(content: str) -> bool:\n"
                "    # Semantic strategy discards greetings and acknowledgments\n"
                "    ...\n"
                "```"
            ),
            (
                "## 9. Where Series 2.4 Fits\n\n"
                "| Lab | Topic | Role in the stack |\n"
                "|-----|-------|-------------------|\n"
                "| 2.1–2.3 | Prune, cache, chunk | Shrink and retrieve external knowledge |\n"
                "| **2.4** | **Conversation Summarization** | **Session memory** — bounded chat context |\n"
                "| 2.5 | Long-Term Memory | Persistent facts across 500 conversations |\n"
                "| 2.6 | Memory Retrieval | Find the right memory from 100k records |\n"
                "| 2.7 | Model Routing | Route to the right model tier |\n\n"
                "---\n\n"
                "## Takeaway\n\n"
                "> **The objective is not to remember every message. "
                "The objective is to remember the right information.**\n\n"
                "**Next lab:** [Series 2.5 — Long-Term Memory](../series-2.5/) — "
                "compress durable user knowledge across hundreds of conversations."
            ),
        ],
    },
    {
        "path": ROOT / "series-2.5/Series_2.5_Long_Term_Memory.ipynb",
        "app_path": "series-2.5/app.py",
        "cells": [
            (
                "# Series 2.5 — Long-Term AI Memory\n\n"
                "**Why AI Fails? — Engineering Lab**\n\n"
                "---\n\n"
                "> Long-term memory is not a conversation archive.  \n"
                "> It is a **compressed knowledge base**.\n\n"
                "**Scenario:** 500 simulated conversations → extract memories → "
                "compress duplicates → retrieve only relevant facts for the prompt.\n\n"
                "**Core lesson:** Conversation history grows forever. Long-term memory shouldn't."
            ),
            (
                "## 1. The Problem\n\n"
                "| Raw memory store | Compressed + retrieved memory |\n"
                "|------------------|-------------------------------|\n"
                "| Every extracted fact stored forever | Dedup, consolidate, expire obsolete entries |\n"
                "| Full profile injected into every prompt | Top-K relevant memories only |\n"
                "| Duplicates (FastAPI mentioned 50 times) | Single canonical preference |\n"
                "| Obsolete facts (PyCharm → VS Code) | Latest wins, old entries dropped |\n\n"
                "### Why this matters in production\n\n"
                "- Personalization requires **remembering user preferences** across sessions\n"
                "- Unbounded memory stores become slow, expensive, and contradictory\n"
                "- The prompt should contain **relevant** memories — not the entire user profile\n\n"
                "**Four strategies compared:**\n\n"
                "```\n"
                "raw        → no compression (baseline)\n"
                "dedup      → same category+key → single memory\n"
                "compressed → dedup + consolidate + update + expire\n"
                "retrieval  → compressed store + top-K for prompt\n"
                "```"
            ),
            (
                "## 2. What is Long-Term AI Memory?\n\n"
                "**Long-term AI memory** stores **durable facts** extracted from many conversations "
                "and injects only **relevant** memories into each new request.\n\n"
                "Unlike session summarization (Series 2.4), long-term memory **persists across sessions** "
                "and must be **compressed** to stay usable.\n\n"
                "### Definition\n\n"
                "```\n"
                "Long-term memory = conversations → extract → compress → store → retrieve top-K → prompt\n"
                "```\n\n"
                "### Compression operations (`memory_compressor.py`)\n\n"
                "| Operation | Example |\n"
                "|-----------|---------|\n"
                "| **Deduplication** | FastAPI mentioned 50× → one memory |\n"
                "| **Consolidation** | FastAPI + Pydantic + SQLAlchemy → Python Backend Stack |\n"
                "| **Updating** | PyCharm → VS Code (latest wins) |\n"
                "| **Expiration** | Drop low-confidence / obsolete entries |\n\n"
                "### What long-term memory is NOT\n\n"
                "| Technique | Difference |\n"
                "|-----------|------------|\n"
                "| **Full chat log** | Memory stores **facts**, not transcripts |\n"
                "| **RAG over docs** | Memory is **user-specific**, not document corpus |\n"
                "| **Session summary** (2.4) | Summaries expire with the session; memory persists |\n\n"
                "> **Enterprise principle:** Treat memory as a **knowledge base** with TTL, "
                "confidence scores, and retrieval — not a dump of every conversation."
            ),
            (
                "## 3. Repository Layout\n\n"
                "```\n"
                "why-ai-fails/\n"
                "├── common/\n"
                "└── series-2.5/\n"
                "    ├── app.py                 ← CLI benchmark entry\n"
                "    ├── conversations.py       ← 500 simulated conversations\n"
                "    ├── memory_extractor.py    ← Extract structured memories\n"
                "    ├── memory_compressor.py   ← Dedup, consolidate, update, expire\n"
                "    ├── memory_store.py        ← JSON profile storage\n"
                "    ├── memory_retriever.py    ← Intent + keyword top-K\n"
                "    ├── evaluator.py           ← Retrieval accuracy\n"
                "    ├── benchmark.py\n"
                "    ├── README.md\n"
                "    └── Series_2.5_Long_Term_Memory.ipynb   ← This notebook\n"
                "```"
            ),
            (
                "## 4. The Memory Pipeline\n\n"
                "```\n"
                "500 Conversations\n"
                "    ↓\n"
                "Memory Extractor\n"
                "    ↓\n"
                "Memory Compressor (dedup → consolidate → update → expire)\n"
                "    ↓\n"
                "Memory Store (JSON profile)\n"
                "    ↓\n"
                "Memory Retriever (top-K by question intent)\n"
                "    ↓\n"
                "Prompt Builder → Gemini\n"
                "```\n\n"
                "| Strategy | CLI | What it does |\n"
                "|----------|-----|--------------|\n"
                "| Raw | `--strategy raw` | Store every extracted memory |\n"
                "| Dedup | `--strategy dedup` | Collapse duplicates |\n"
                "| Compressed | `--strategy compressed` | Full compression pipeline |\n"
                "| Retrieval | `--strategy retrieval` | Compressed + top-K in prompt |"
            ),
            (
                "## 5. Three Layers of Memory Engineering\n\n"
                "### Layer 1 — Extract structured facts\n\n"
                "Memories have `category`, `key`, `value`, `confidence`, and optional TTL — "
                "not free-form chat replay.\n\n"
                "---\n\n"
                "### Layer 2 — Compress the store\n\n"
                "Without compression, 500 conversations produce thousands of redundant memories. "
                "Consolidation merges related stack items; expiration drops stale entries.\n\n"
                "---\n\n"
                "### Layer 3 — Retrieve + measure\n\n"
                "| Metric | What it tells you |\n"
                "|--------|-------------------|\n"
                "| **Memory size** | Tokens in compressed store |\n"
                "| **Prompt tokens** | Only top-K injected |\n"
                "| **Retrieval accuracy** | Expected memories found / total |\n"
                "| **Personalization** | Question-specific memory match |\n\n"
                "| Mode | Flag | API key? |\n"
                "|------|------|----------|\n"
                "| **Dry-run** | `--dry-run` | No — **$0** |\n"
                "| **Live** | (none) | Yes |"
            ),
            (
                "## 6. Execution Flow\n\n"
                "```\n"
                "Parse CLI (--strategy, --question-id, --conversations, --top-k)\n"
                "    │\n"
                "    └─ Load N conversations (default 500)\n"
                "            → extract memories\n"
                "            → apply strategy (raw / dedup / compressed / retrieval)\n"
                "            → build prompt with memories\n"
                "            → evaluate retrieval accuracy\n"
                "            └─ print_benchmark()\n"
                "```"
            ),
            (
                "## 7. How to Run\n\n"
                "From the **repo root**:\n\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "cp .env.example .env   # optional\n"
                "```\n\n"
                "| Command | What it does | API key? |\n"
                "|---------|--------------|----------|\n"
                "| `python series-2.5/app.py --dry-run` | All four strategies | No |\n"
                "| `python series-2.5/app.py --strategy retrieval --dry-run` | Best strategy | No |\n"
                "| `python series-2.5/app.py --conversations 100 --dry-run` | Faster dev test | No |\n"
                "| `python series-2.5/app.py` | Live Gemini | Yes |"
            ),
            (
                "## 8. Key Code Snippets\n\n"
                "### Deduplication (`memory_compressor.py`)\n\n"
                "```python\n"
                "def deduplicate(memories):\n"
                "    # Same category+key → keep highest conversation_id / confidence\n"
                "    best = {}\n"
                "    for mem in memories:\n"
                "        slot = (mem[\"category\"], mem[\"key\"])\n"
                "        ...\n"
                "    return list(best.values())\n"
                "```\n\n"
                "### Consolidation\n\n"
                "```python\n"
                "CONSOLIDATED_VALUE = \"Python Backend Stack (FastAPI, Pydantic, SQLAlchemy)\"\n"
                "# FastAPI + Pydantic + SQLAlchemy → single backend_stack memory\n"
                "```"
            ),
            (
                "## 9. Where Series 2.5 Fits\n\n"
                "| Lab | Topic | Role |\n"
                "|-----|-------|------|\n"
                "| 2.4 | Conversation Summarization | Session-scoped memory |\n"
                "| **2.5** | **Long-Term Memory** | **Build & compress** persistent user profile |\n"
                "| 2.6 | Memory Retrieval | **Find** the right memory from 100k records |\n"
                "| 2.7 | Model Routing | Select model tier per request |\n\n"
                "---\n\n"
                "## Takeaway\n\n"
                "> **Store efficiently. Retrieve precisely. Never dump the full profile into every prompt.**\n\n"
                "**Next lab:** [Series 2.6 — Memory Retrieval](../series-2.6/) — "
                "finding the right memory from a 100,000-record store."
            ),
        ],
    },
    {
        "path": ROOT / "series-2.6/Series_2.6_Memory_Retrieval.ipynb",
        "app_path": "series-2.6/app.py",
        "cells": [
            (
                "# Series 2.6 — Memory Retrieval\n\n"
                "**Why AI Fails? — Engineering Lab**\n\n"
                "---\n\n"
                "> Building memory is only half of the problem.  \n"
                "> **Retrieving the right memory** is what makes AI intelligent.\n\n"
                "**Scenario:** 100,000 synthetic memory records — four retrieval strategies, "
                "precision/recall benchmarks, top-K injection into the prompt.\n\n"
                "**Core lesson:** Memory is valuable only when it can be **found**."
            ),
            (
                "## 1. The Problem\n\n"
                "| Naive memory search | Intelligent retrieval |\n"
                "|---------------------|----------------------|\n"
                "| Keyword match only → misses synonyms | Semantic search finds related concepts |\n"
                "| Inject entire 100k store into prompt | Top-K relevant memories only |\n"
                "| No ranking → stale or duplicate facts win | Re-ranking by confidence, recency, priority |\n"
                "| One strategy for all queries | Hybrid + re-rank for enterprise accuracy |\n\n"
                "### Why this matters in production\n\n"
                "- Series 2.5 showed **how to build and compress** memory\n"
                "- At scale, **search quality** determines personalization quality\n"
                "- Wrong retrieval → wrong prompt context → wrong answers\n\n"
                "**Four strategies:**\n\n"
                "```\n"
                "keyword  → inverted index, exact term overlap (fast)\n"
                "semantic → TF-IDF cosine similarity\n"
                "hybrid   → keyword + semantic + metadata boost\n"
                "rerank   → hybrid top-20 → ranking formula → top-K\n"
                "```"
            ),
            (
                "## 2. What is Memory Retrieval?\n\n"
                "**Memory retrieval** selects the **most relevant** long-term memories for a user request "
                "from a large store — without loading the entire profile into the prompt.\n\n"
                "### Definition\n\n"
                "```\n"
                "Memory retrieval = query → intent → search → rank → top-K → prompt\n"
                "```\n\n"
                "### Ranking formula (re-ranking strategy)\n\n"
                "```\n"
                "Memory Score = Semantic Similarity + Confidence + Recency + Business Priority\n"
                "```\n\n"
                "### Dataset characteristics (100k records)\n\n"
                "- Categories: User Profile, Policies, Project Knowledge, Security, Database, …\n"
                "- Includes duplicates, noise, obsolete entries (Flask, MySQL), conflicting preferences\n"
                "- Tests whether retrieval finds **canonical** facts under realistic messiness\n\n"
                "### What memory retrieval is NOT\n\n"
                "| Technique | Difference |\n"
                "|-----------|------------|\n"
                "| **Memory compression** (2.5) | Compression shrinks the **store**; retrieval selects **what to inject** |\n"
                "| **RAG chunking** (2.3) | RAG retrieves **documents**; this retrieves **user memories** |\n"
                "| **Vector DB product** | This lab uses readable keyword + TF-IDF — no black box |"
            ),
            (
                "## 3. Repository Layout\n\n"
                "```\n"
                "why-ai-fails/\n"
                "├── common/\n"
                "└── series-2.6/\n"
                "    ├── app.py           ← CLI benchmark entry\n"
                "    ├── memories.py      ← 100k memory generator\n"
                "    ├── memory_store.py  ← Inverted index + TF-IDF\n"
                "    ├── retriever.py     ← Four retrieval strategies\n"
                "    ├── ranking.py       ← Re-ranking + top-K\n"
                "    ├── evaluator.py     ← Precision, recall, accuracy\n"
                "    ├── queries.py       ← Benchmark queries\n"
                "    ├── benchmark.py\n"
                "    ├── README.md\n"
                "    └── Series_2.6_Memory_Retrieval.ipynb   ← This notebook\n"
                "```"
            ),
            (
                "## 4. The Retrieval Pipeline (`retriever.py`)\n\n"
                "```\n"
                "User Request\n"
                "    ↓\n"
                "Intent Detection\n"
                "    ↓\n"
                "Memory Search (keyword / semantic / hybrid)\n"
                "    ↓\n"
                "Memory Ranking (re-rank strategy)\n"
                "    ↓\n"
                "Top-K Selection\n"
                "    ↓\n"
                "Prompt Builder → Gemini\n"
                "```\n\n"
                "| Strategy | CLI | Candidate pool |\n"
                "|----------|-----|----------------|\n"
                "| Keyword | `--strategy keyword` | Inverted index, top 200 |\n"
                "| Semantic | `--strategy semantic` | TF-IDF sample 5000 |\n"
                "| Hybrid | `--strategy hybrid` | Combined scoring, top 300 |\n"
                "| Re-rank | `--strategy rerank` | Hybrid top 20 → full formula |"
            ),
            (
                "## 5. Three Layers of Retrieval Engineering\n\n"
                "### Layer 1 — Search (cast a wide net)\n\n"
                "Keyword search is fast and exact. Semantic search finds related terms "
                "(e.g. \"postgres\" → PostgreSQL). Hybrid combines both.\n\n"
                "---\n\n"
                "### Layer 2 — Rank (pick the best memories)\n\n"
                "Re-ranking boosts confidence, recency, and business priority — "
                "so stale Flask preferences don't beat current FastAPI facts.\n\n"
                "---\n\n"
                "### Layer 3 — Measure (precision, recall, prompt tokens)\n\n"
                "| Metric | What it tells you |\n"
                "|--------|-------------------|\n"
                "| **Retrieval accuracy** | Expected values in top-K |\n"
                "| **Precision** | Relevant / retrieved |\n"
                "| **Recall** | Canonical facts recovered |\n"
                "| **Prompt tokens** | Only top-K injected — not 100k |\n\n"
                "| Mode | Flag | API key? |\n"
                "|------|------|----------|\n"
                "| **Dry-run** | `--dry-run` | No — **$0** |\n"
                "| **Live** | (none) | Yes |"
            ),
            (
                "## 6. Execution Flow\n\n"
                "```\n"
                "Parse CLI (--strategy, --query-id, --top-k, --memories)\n"
                "    │\n"
                "    └─ Build MemoryStore (default 100,000 records)\n"
                "            For each benchmark query:\n"
                "                detect_intent() → retrieve → rank → top-K\n"
                "                evaluate precision / recall / accuracy\n"
                "            └─ print_benchmark()\n"
                "```"
            ),
            (
                "## 7. How to Run\n\n"
                "From the **repo root**:\n\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "cp .env.example .env   # optional\n"
                "```\n\n"
                "| Command | What it does | API key? |\n"
                "|---------|--------------|----------|\n"
                "| `python series-2.6/app.py --dry-run` | All four strategies | No |\n"
                "| `python series-2.6/app.py --strategy rerank --dry-run` | Best strategy | No |\n"
                "| `python series-2.6/app.py --memories 10000 --dry-run` | Faster dev test | No |\n"
                "| `python series-2.6/app.py` | Live Gemini | Yes |"
            ),
            (
                "## 8. Key Code Snippets\n\n"
                "### Intent detection (`retriever.py`)\n\n"
                "```python\n"
                "def detect_intent(query: str) -> set[str]:\n"
                "    return set(_tokenize(query))\n"
                "```\n\n"
                "### Strategy names\n\n"
                "```python\n"
                "STRATEGIES = (\"keyword\", \"semantic\", \"hybrid\", \"rerank\")\n"
                "RERANK_POOL = 20  # hybrid top-20 before full ranking formula\n"
                "```"
            ),
            (
                "## 9. Where Series 2.6 Fits\n\n"
                "| Lab | Topic | Role |\n"
                "|-----|-------|------|\n"
                "| 2.5 | Long-Term Memory | Build & compress the store |\n"
                "| **2.6** | **Memory Retrieval** | **Find** the right memory at scale |\n"
                "| 2.7 | Model Routing | Route to the right model tier |\n\n"
                "---\n\n"
                "## Takeaway\n\n"
                "> **Store efficiently (2.5). Retrieve precisely (2.6).**\n\n"
                "**Next lab:** [Series 2.7 — Model Routing](../series-2.7/) — "
                "select the right LLM for each request, not the biggest model every time."
            ),
        ],
    },
    {
        "path": ROOT / "series-2.7/Series_2.7_Model_Routing.ipynb",
        "app_path": "series-2.7/app.py",
        "cells": [
            (
                "# Series 2.7 — Model Routing\n\n"
                "**Why AI Fails? — Engineering Lab**\n\n"
                "---\n\n"
                "> Enterprise AI becomes efficient by selecting the **right model** — "
                "not the biggest model every time.\n\n"
                "**Scenario:** 1,000 synthetic AI requests across translation, SQL, code review, "
                "architecture, legal analysis, and vision — four routing strategies.\n\n"
                "**Core lesson:** The best AI system knows **when** to use the large model."
            ),
            (
                "## 1. The Problem\n\n"
                "| Single-model baseline | Intelligent routing |\n"
                "|-----------------------|---------------------|\n"
                "| Every request → large general LLM | Simple tasks → small / medium models |\n"
                "| Highest cost on every call | Average cost drops dramatically |\n"
                "| Same latency for \"translate hello\" and \"design architecture\" | Latency matches task complexity |\n"
                "| No escalation path | Confidence routing escalates only when needed |\n\n"
                "### Why this matters in production\n\n"
                "- Most enterprise traffic is **simple** (classification, translation, summarization)\n"
                "- Routing wrong → either **overpay** (small task on large model) or **under-serve** (complex task on small model)\n"
                "- Security policy may require **internal** models for confidential code\n\n"
                "**Four strategies:**\n\n"
                "```\n"
                "single     → everything to large general LLM (baseline)\n"
                "rules      → static task-type → model map\n"
                "dynamic    → score models on intent, complexity, cost, latency\n"
                "confidence → start cheap; escalate when confidence is low\n"
                "```"
            ),
            (
                "## 2. What is Model Routing?\n\n"
                "**Model routing** selects which LLM (or model tier) handles each request based on "
                "task type, complexity, cost, latency, and security policy.\n\n"
                "### Definition\n\n"
                "```\n"
                "Model routing = request → classify → estimate complexity → policy check → pick model → respond\n"
                "```\n\n"
                "### Model pool in this lab\n\n"
                "| Model | Best for |\n"
                "|-------|----------|\n"
                "| Small Language Model | Translation, classification, summarization |\n"
                "| Medium Coding Model | SQL, API development, code review |\n"
                "| Medium Coding (Internal) | Restricted / confidential code |\n"
                "| Large Reasoning Model | Architecture, legal, complex reasoning |\n"
                "| Vision Model | Image analysis |\n"
                "| Large General LLM | Baseline — all tasks, highest cost |\n\n"
                "### What model routing is NOT\n\n"
                "| Technique | Difference |\n"
                "|-----------|------------|\n"
                "| **Smaller prompt** (2.1–2.6) | Routing picks the **model**; prior labs shrink **input** |\n"
                "| **Load balancing** | Routing is **task-aware**, not round-robin |\n"
                "| **Fallback on error** | Confidence routing escalates on **low confidence**, not API failure only |"
            ),
            (
                "## 3. Repository Layout\n\n"
                "```\n"
                "why-ai-fails/\n"
                "├── common/\n"
                "└── series-2.7/\n"
                "    ├── app.py           ← CLI benchmark entry\n"
                "    ├── models.py        ← Model pool (cost, latency, strengths)\n"
                "    ├── requests.py      ← 1,000 synthetic AI requests\n"
                "    ├── classifier.py    ← Intent + task classification\n"
                "    ├── complexity.py    ← Simple / medium / complex\n"
                "    ├── policy.py        ← Security + budget rules\n"
                "    ├── router.py        ← Four routing strategies\n"
                "    ├── evaluator.py     ← Accuracy, utilization, escalation\n"
                "    ├── benchmark.py\n"
                "    ├── README.md\n"
                "    └── Series_2.7_Model_Routing.ipynb   ← This notebook\n"
                "```"
            ),
            (
                "## 4. The Routing Pipeline (`router.py`)\n\n"
                "```\n"
                "User Request\n"
                "    ↓\n"
                "Intent Detection + Task Classification\n"
                "    ↓\n"
                "Complexity Estimation\n"
                "    ↓\n"
                "Security Policy + Cost Evaluation\n"
                "    ↓\n"
                "Model Router (single / rules / dynamic / confidence)\n"
                "    ↓\n"
                "Best Model → Response\n"
                "```\n\n"
                "| Strategy | CLI | Approach |\n"
                "|----------|-----|----------|\n"
                "| Single | `--strategy single` | Baseline — all → large general |\n"
                "| Rules | `--strategy rules` | Static `RULE_MAP` by task type |\n"
                "| Dynamic | `--strategy dynamic` | Score all allowed models |\n"
                "| Confidence | `--strategy confidence` | Cheap first; escalate one tier if confidence < 0.72 |"
            ),
            (
                "## 5. Three Layers of Routing Engineering\n\n"
                "### Layer 1 — Classify the request\n\n"
                "`classifier.py` detects intent and task type from the request text. "
                "Wrong classification → wrong route.\n\n"
                "---\n\n"
                "### Layer 2 — Apply policy and score models\n\n"
                "Security policy restricts confidential code to internal models. "
                "Dynamic routing scores remaining models on fit, cost, and latency.\n\n"
                "---\n\n"
                "### Layer 3 — Measure accuracy vs cost\n\n"
                "| Metric | What it tells you |\n"
                "|--------|-------------------|\n"
                "| **Routing accuracy** | Model matches expected tier |\n"
                "| **Average cost** | Mean estimated cost per request |\n"
                "| **Model utilization** | Traffic distribution across pool |\n"
                "| **Escalation rate** | Confidence routing upgrades |\n\n"
                "| Mode | Flag | API key? |\n"
                "|------|------|----------|\n"
                "| **Dry-run** | `--dry-run` | No — **$0** |\n"
                "| **Live** | (none) | Yes — single request demo |"
            ),
            (
                "## 6. Execution Flow\n\n"
                "```\n"
                "Parse CLI (--strategy, --request-id, --requests)\n"
                "    │\n"
                "    └─ Load request dataset (default 1,000)\n"
                "            For each request (or one via --request-id):\n"
                "                classify_task() → estimate_complexity()\n"
                "                apply_security_policy() → route()\n"
                "                evaluate accuracy + cost\n"
                "            └─ print_benchmark()\n"
                "```"
            ),
            (
                "## 7. How to Run\n\n"
                "From the **repo root**:\n\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "cp .env.example .env   # optional\n"
                "```\n\n"
                "| Command | What it does | API key? |\n"
                "|---------|--------------|----------|\n"
                "| `python series-2.7/app.py --dry-run` | All four strategies on 1k requests | No |\n"
                "| `python series-2.7/app.py --strategy confidence --dry-run` | Escalation routing | No |\n"
                "| `python series-2.7/app.py --request-id r0025 --dry-run` | Inspect one request | No |\n"
                "| `python series-2.7/app.py --requests 100 --dry-run` | Faster dev test | No |"
            ),
            (
                "## 8. Key Code Snippets\n\n"
                "### Rule map (`router.py`)\n\n"
                "```python\n"
                "RULE_MAP = {\n"
                "    \"translation\": \"small\",\n"
                "    \"sql_generation\": \"medium_coding\",\n"
                "    \"architecture_design\": \"large_reasoning\",\n"
                "    ...\n"
                "}\n"
                "```\n\n"
                "### Confidence escalation\n\n"
                "```python\n"
                "CONFIDENCE_THRESHOLD = 0.72\n"
                "ESCALATION_STEP = {\n"
                "    \"small\": \"medium_coding\",\n"
                "    \"medium_coding\": \"large_reasoning\",\n"
                "    ...\n"
                "}\n"
                "```"
            ),
            (
                "## 9. Where Series 2.7 Fits\n\n"
                "Series 2.7 **completes the cost stack**:\n\n"
                "| Lab | Layer |\n"
                "|-----|-------|\n"
                "| 2.1 | Prune evidence |\n"
                "| 2.2 | Cache stable prompts |\n"
                "| 2.3 | Chunk & retrieve documents |\n"
                "| 2.4 | Summarize conversations |\n"
                "| 2.5 | Compress long-term memory |\n"
                "| 2.6 | Retrieve memories at scale |\n"
                "| **2.7** | **Route to the right model** |\n\n"
                "---\n\n"
                "## Takeaway\n\n"
                "> **Select the right model — not the biggest model.**  \n"
                "> Prune, cache, retrieve, summarize — then route what remains.\n\n"
                "**Previous lab:** [Series 2.6 — Memory Retrieval](../series-2.6/)"
            ),
        ],
    },
]


def make_notebook(spec: dict) -> dict:
    cells = []
    md_sources = spec["cells"]
    how_to_run_idx = 7  # insert demo cell after "How to Run"

    for i, source in enumerate(md_sources):
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": source,
                "id": f"cell-{i:02d}",
            }
        )
        if i == how_to_run_idx:
            # Insert code cell after "How to Run"
            cells.append(
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": DEMO_CELL.replace("{app_path}", spec["app_path"]),
                    "execution_count": None,
                    "outputs": [],
                    "id": "demo-cell",
                }
            )

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    from add_python_file_sections import patch_notebook

    for spec in NOTEBOOKS:
        path = spec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        nb = make_notebook(spec)
        path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")
        series_key = path.parent.name
        patch_notebook(series_key, path)


if __name__ == "__main__":
    main()
