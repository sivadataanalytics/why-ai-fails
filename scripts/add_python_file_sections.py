#!/usr/bin/env python3
"""Insert 'Python Files in This Lab' section into all series presentation notebooks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYTHON_FILE_SECTIONS: dict[str, str] = {
    "series-2.1": (
        "## 4. Python Files in This Lab\n\n"
        "Files under `series-2.1/` plus shared modules from `common/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Runs **two flows** side-by-side (with/without pruning), "
        "handles `--dry-run` and `--clarify-demo`, loads HDFS logs, calls Gemini or token estimator, "
        "prints the benchmark report. |\n"
        "| **`prune.py`** | The 5-step pruning pipeline: `filter_logs_for_block()` → "
        "`keep_useful_columns()` → `deduplicate_messages()` → `limit_relevant_rows()` → "
        "`summarize_evidence()`. Orchestrated by `prune_hdfs_context()`. |\n\n"
        "**Shared (`common/`):**\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| `prompt_builder.py` | `build_unpruned_prompt()` (anti-pattern) vs `build_pruned_prompt()` "
        "(compact evidence dict). |\n"
        "| `benchmark.py` | Side-by-side printer — prompt tokens, latency, savings %. |\n"
        "| `gemini_client.py` | Wrapper around Gemini API for live runs. |\n"
        "| `token_usage.py` | `estimate_tokens()` for dry-run ($0) token math. |\n"
        "| `utils.py` | `load_hdfs_logs()`, `extract_block_id()`, `is_ambiguous_question()`. |\n\n"
        "**Repo root:** `demo.py` delegates to `series-2.1/app.py` for convenience."
    ),
    "series-2.2": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.2/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Splits prompt into **static** (cacheable) and **dynamic** "
        "(per-request) layers, runs without-cache vs with-cache flows, supports `--drift-demo` "
        "and `--cache-version`. |\n"
        "| **`prompt_cache.py`** | Cache engine — `PromptCache.resolve()` tracks hits/misses, "
        "`billable_tokens()` applies cheaper cache-read pricing, `build_static_prompt()` assembles "
        "versioned static blocks (`STATIC_PROMPTS` v1/v2/v3). |\n"
        "| **`benchmark.py`** | Side-by-side printer for cache savings — prompt tokens, cache hit rate, "
        "estimated cost reduction. |\n\n"
        "**Also uses `common/`:** `gemini_client.py`, `token_usage.py`, `prompt_builder.py` "
        "(pruned evidence from Series 2.1 pattern)."
    ),
    "series-2.3": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.3/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Loads `docs/` corpus, runs all chunking strategies "
        "and benchmark questions, calls Gemini (or `--dry-run`), prints comparison. |\n"
        "| **`chunker.py`** | Document splitting — fixed-size strategies (`small`/`medium`/`large` "
        "with overlap) and `semantic` (split on `#` headings). Exposes `STRATEGIES` config. |\n"
        "| **`retriever.py`** | Keyword retriever (no vector DB). `score_chunk()` ranks by term overlap, "
        "`retrieve_top_k()` selects chunks, `compute_hit_score()` measures retrieval quality. |\n"
        "| **`questions.py`** | Benchmark questions (`q1`–`q3`) with `expected_terms` for Hit Score. |\n"
        "| **`prompt_builder.py`** | `build_rag_prompt()` — assembles user question + labeled retrieved "
        "chunks into the final Gemini prompt. |\n"
        "| **`benchmark.py`** | Side-by-side strategy printer — Hit Score, prompt tokens, latency, cost. |"
    ),
    "series-2.4": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.4/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Loads the 175-message conversation, runs all four "
        "summarization strategies, evaluates memory scores, prints benchmark. |\n"
        "| **`conversation_dataset.py`** | Generates the synthetic ~175-message enterprise coding "
        "assistant thread with embedded facts, noise, and `BENCHMARK_QUESTIONS`. |\n"
        "| **`conversation_loader.py`** | Thin wrapper — `load_conversation()` returns the message list. |\n"
        "| **`summarizer.py`** | Four local summarization strategies: `full`, `rolling`, `hierarchical`, "
        "`semantic`. Builds compressed memory + recent message window (no LLM needed for dry-run). |\n"
        "| **`memory.py`** | Structured fact extraction for semantic strategy — `ConversationMemory`, "
        "`extract_memory()`, filters greetings/thanks noise. |\n"
        "| **`evaluator.py`** | `memory_score()` — remembered facts / expected facts; "
        "context retention vs full conversation baseline. |\n"
        "| **`prompts.py`** | `build_answer_prompt()` — full history vs summary + latest messages. |\n"
        "| **`benchmark.py`** | Side-by-side printer for all four strategies. |"
    ),
    "series-2.5": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.5/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Runs the full pipeline across four memory strategies "
        "(raw → dedup → compressed → retrieval), prints benchmark. |\n"
        "| **`conversations.py`** | Generates 500 simulated conversations with duplicates, changing "
        "preferences, TTL entries, and `EXPECTED_MEMORIES` for evaluation. |\n"
        "| **`conversation_loader.py`** | `load_conversations()` — loads N conversations for processing. |\n"
        "| **`memory_extractor.py`** | Regex-based extraction of structured memories (preferences, "
        "frameworks, security rules) from user turns via `EXTRACTION_RULES`. |\n"
        "| **`memory_compressor.py`** | Four compression ops: `deduplicate()`, `consolidate()`, "
        "update (latest wins), and expire (drop low-confidence/obsolete). |\n"
        "| **`memory_store.py`** | `MemoryStore` — JSON profile storage for compressed knowledge base. |\n"
        "| **`memory_retriever.py`** | Intent + keyword retrieval — `detect_intents()`, ranks memories "
        "by question relevance, returns top-K. |\n"
        "| **`evaluator.py`** | `retrieval_accuracy()` and personalization metrics vs expected memories. |\n"
        "| **`prompts.py`** | `build_memory_prompt()` — injects only retrieved memories into prompt. |\n"
        "| **`benchmark.py`** | Side-by-side strategy comparison printer. |"
    ),
    "series-2.6": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.6/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Builds 100k memory store, runs four retrieval strategies "
        "on benchmark queries, prints precision/recall/accuracy. |\n"
        "| **`memories.py`** | Generates 100,000 synthetic memory records with duplicates, noise, "
        "obsolete entries, and `EXPECTED_MEMORIES` ground truth. |\n"
        "| **`memory_store.py`** | `MemoryStore` — inverted index for keyword search + IDF weights "
        "for TF-IDF semantic scoring. |\n"
        "| **`retriever.py`** | Four strategies: `keyword`, `semantic`, `hybrid`, `rerank`. "
        "Includes `detect_intent()` and candidate pool sizing. |\n"
        "| **`ranking.py`** | Re-ranking formula: semantic + confidence + recency + business priority. "
        "`rerank()`, `select_top_k()`. |\n"
        "| **`queries.py`** | Benchmark queries (`q1`–`q5`) with expected values and intent keywords. |\n"
        "| **`evaluator.py`** | Precision, recall, retrieval accuracy, personalization metrics. |\n"
        "| **`prompts.py`** | `build_retrieval_prompt()` — injects top-K memories only (not 100k). |\n"
        "| **`benchmark.py`** | Side-by-side retrieval strategy comparison printer. |"
    ),
    "series-2.7": (
        "## 4. Python Files in This Lab\n\n"
        "Every `.py` file under `series-2.7/`:\n\n"
        "| File | What it does |\n"
        "|------|--------------|\n"
        "| **`app.py`** | CLI entry point. Routes 1,000 requests through four strategies, "
        "aggregates cost/latency/accuracy, supports `--request-id` inspection. |\n"
        "| **`models.py`** | Enterprise model pool — `MODELS` dict with cost, latency, quality, "
        "capabilities; `get_model()`, `estimate_model_cost()`. |\n"
        "| **`requests.py`** | Generates 1,000 synthetic AI requests with task type, complexity, "
        "security level, and expected model tier. |\n"
        "| **`classifier.py`** | Keyword-based `detect_intent()` and `classify_task()` — no ML deps. |\n"
        "| **`complexity.py`** | `estimate_complexity()` — simple / medium / complex from prompt signals. |\n"
        "| **`policy.py`** | Security + budget rules — `allowed_models()`, `apply_security_policy()` "
        "restricts internal/confidential code to approved models. |\n"
        "| **`router.py`** | Four routing strategies: `single`, `rules`, `dynamic`, `confidence`. "
        "`route_request()`, static `RULE_MAP`, escalation ladder. |\n"
        "| **`evaluator.py`** | Routing accuracy, model utilization %, escalation rate aggregation. |\n"
        "| **`prompts.py`** | `build_routing_prompt()` for live Gemini execution of routed requests. |\n"
        "| **`benchmark.py`** | `run_strategy()`, side-by-side comparison and utilization report. |"
    ),
}

NOTEBOOK_PATHS = {
    "series-2.1": ROOT / "series-2.1/Series_2.1_Context_Pruning.ipynb",
    "series-2.2": ROOT / "series-2.2/Series_2.2_Prompt_Caching.ipynb",
    "series-2.3": ROOT / "series-2.3/Series_2.3_RAG_Chunking.ipynb",
    "series-2.4": ROOT / "series-2.4/Series_2.4_Conversation_Summarization.ipynb",
    "series-2.5": ROOT / "series-2.5/Series_2.5_Long_Term_Memory.ipynb",
    "series-2.6": ROOT / "series-2.6/Series_2.6_Memory_Retrieval.ipynb",
    "series-2.7": ROOT / "series-2.7/Series_2.7_Model_Routing.ipynb",
}

SECTION_RE = re.compile(r"^## (\d+)\. ", re.MULTILINE)


def to_source_list(text: str) -> list[str]:
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def cell_text(cell: dict) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src or ""


def renumber_sections(source: str, offset: int = 1) -> str:
    """Bump ## N. headings by offset (for sections >= 4)."""

    def repl(match: re.Match[str]) -> str:
        num = int(match.group(1))
        if num >= 4:
            return f"## {num + offset}. "
        return match.group(0)

    return SECTION_RE.sub(repl, source)


def patch_notebook(series_key: str, path: Path) -> None:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # Skip if already patched
    for cell in cells:
        if cell.get("cell_type") == "markdown" and "## 4. Python Files in This Lab" in cell_text(cell):
            print(f"Skip (already patched): {path.relative_to(ROOT)}")
            return

    # Find Repository Layout cell (section 3)
    layout_idx: int | None = None
    for i, cell in enumerate(cells):
        if cell.get("cell_type") == "markdown" and "## 3. Repository Layout" in cell_text(cell):
            layout_idx = i
            break

    if layout_idx is None:
        raise ValueError(f"No Repository Layout section in {path}")

    # Renumber sections 4+ in all markdown cells after layout
    for i in range(layout_idx + 1, len(cells)):
        cell = cells[i]
        if cell.get("cell_type") != "markdown":
            continue
        cell["source"] = to_source_list(renumber_sections(cell_text(cell)))

    # Insert new section after layout
    new_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": to_source_list(PYTHON_FILE_SECTIONS[series_key]),
        "id": f"python-files-{series_key}",
    }
    cells.insert(layout_idx + 1, new_cell)

    path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched {path.relative_to(ROOT)}")


def main() -> None:
    for key, path in NOTEBOOK_PATHS.items():
        patch_notebook(key, path)


if __name__ == "__main__":
    main()
