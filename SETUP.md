# One-Time Setup — Why AI Fails? Engineering Labs

Complete setup guide for Series 2.1 through 2.6.  
Do this **once** on your machine; every lab reuses the same environment.

---

## What you need

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.10+ | 3.11 or 3.12 |
| **Git** | Any recent version | Latest |
| **Disk space** | ~200 MB | ~500 MB (venv + deps) |
| **Internet** | For `pip install` and clone | — |
| **Gemini API key** | Optional | Required only for **live** LLM runs |

> **Students without an API key:** Every lab supports `--dry-run` — full benchmarks at **$0** with no API call.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/sivadataanalytics/why-ai-fails.git
cd why-ai-fails
```

If you already have the repo locally:

```bash
cd "/path/to/why-ai-fails"
git pull origin main
```

---

## Step 2 — Check Python

```bash
python3 --version
```

Expected: `Python 3.10.x` or higher.

If `python3` is missing:

- **macOS:** `brew install python@3.12`
- **Ubuntu/Debian:** `sudo apt install python3 python3-venv python3-pip`
- **Windows:** Install from [python.org](https://www.python.org/downloads/) and enable “Add Python to PATH”

---

## Step 3 — Create a virtual environment (recommended)

A virtual environment keeps lab dependencies isolated from your system Python.

```bash
# From repo root
python3 -m venv .venv
```

**Activate the environment:**

| OS | Command |
|----|---------|
| macOS / Linux | `source .venv/bin/activate` |
| Windows (Cmd) | `.venv\Scripts\activate.bat` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

Your shell prompt should show `(.venv)`.

**Deactivate later (optional):**

```bash
deactivate
```

---

## Step 4 — Install dependencies

With the virtual environment activated:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Packages installed:**

| Package | Purpose |
|---------|---------|
| `google-genai` | Gemini API client (live runs only) |
| `python-dotenv` | Load `GEMINI_API_KEY` from `.env` |
| `pandas` | Log parsing and pruning (Series 2.1 / 2.2) |

Verify:

```bash
python3 -c "import pandas; import dotenv; print('Dependencies OK')"
```

---

## Step 5 — Configure API key (optional)

Required **only** if you want live Gemini answers. Dry-runs work without this step.

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Get a free key: [Google AI Studio](https://aistudio.google.com/apikey)

**Security:**

- Never commit `.env` to git (it is already in `.gitignore`)
- Never paste API keys into notebooks or slide decks

---

## Step 6 — Verify each lab (dry-run, $0)

Run these from the **repo root** with your venv activated.

### Series 2.1 — Context Pruning

```bash
python3 demo.py --dry-run
```

Expected: ~71,000 tokens without pruning → ~200 with pruning (~99% savings).

Other commands:

```bash
python3 demo.py --clarify-demo          # Layer 1: scoping questions, 0 tokens
python3 series-2.1/app.py --dry-run     # Same lab, direct entry
```

Presentation notebook: `series-2.1/Series_2.1_Context_Pruning.ipynb`

---

### Series 2.2 — Prompt Caching

```bash
python3 series-2.2/app.py --dry-run
```

Expected: ~510 prompt tokens without cache → ~156 with cache hit.

Other commands:

```bash
python3 series-2.2/app.py --drift-demo              # v1/v2/v3 cache size comparison
python3 series-2.2/app.py --cache-version v3 --dry-run
```

Presentation notebook: `series-2.2/Series_2.2_Prompt_Caching.ipynb`

---

### Series 2.3 — RAG Chunking

```bash
python3 series-2.3/app.py --dry-run
```

Uses article corpus in `docs/`.

Presentation notebook: `series-2.3/Series_2.3_RAG_Chunking.ipynb`

---

### Series 2.4 — Conversation Summarization

```bash
python3 series-2.4/app.py --dry-run
```

Uses synthetic conversation in `series-2.4/conversation_dataset.py`.

Presentation notebook: `series-2.4/Series_2.4_Conversation_Summarization.ipynb`

---

### Series 2.5 — Long-Term Memory

```bash
python3 series-2.5/app.py --dry-run
```

Uses 500 simulated conversations in `series-2.5/conversations.py`.

Presentation notebook: `series-2.5/Series_2.5_Long_Term_Memory.ipynb`

---

### Series 2.6 — Memory Retrieval

```bash
python3 series-2.6/app.py --dry-run
```

Indexes 100,000 synthetic memories (~0.5s on a typical laptop).

Faster dev test (smaller store):

```bash
python3 series-2.6/app.py --memories 10000 --dry-run
```

Presentation notebook: `series-2.6/Series_2.6_Memory_Retrieval.ipynb`

---

### Series 2.7 — Model Routing

```bash
python3 series-2.7/app.py --dry-run
```

Routes 1,000 synthetic requests across four strategies.

Presentation notebook: `series-2.7/Series_2.7_Model_Routing.ipynb`

---

### Series 2.8 — Multi-Agent Orchestration

```bash
python3 series-2.8/app.py --dry-run
```

500 enterprise requests; compares single, sequential, parallel, and reviewer strategies.

Other commands:

```bash
python3 series-2.8/app.py --strategy reviewer --dry-run
python3 series-2.8/app.py --request-id r0024 --dry-run
python3 series-2.8/app.py --requests 100 --dry-run
```

Presentation notebook: `series-2.8/Series_2.8_Multi_Agent_Orchestration.ipynb`

---

## Step 7 — Presentation notebooks (optional)

For classroom or demo presentations:

1. Open Cursor / VS Code / Jupyter
2. Open the `.ipynb` file under any `series-2.x/` folder
3. Select the Python kernel tied to your `.venv`
4. Run cells top to bottom; demo cells call `--dry-run` automatically

Available notebooks: `Series_2.1` through `Series_2.8` (one per lab).

**Jupyter (if not using VS Code/Cursor):**

```bash
pip install jupyter
jupyter notebook series-2.1/Series_2.1_Context_Pruning.ipynb
```

### Validate notebooks (before push)

GitHub shows **Invalid Notebook** if cell IDs or source format break the Jupyter schema (e.g. IDs with `.` in them).

```bash
# Validate all presentation notebooks
python3 scripts/validate_notebooks.py

# Auto-fix common issues (source format, invalid cell IDs)
python3 scripts/validate_notebooks.py --fix
```

**Optional — block bad pushes automatically:**

```bash
./scripts/install_git_hooks.sh   # one-time: enables .githooks/pre-push
```

After that, `git push` runs validation first and aborts if any notebook fails.

---

## Step 8 — Live Gemini runs (optional)

When `.env` contains a valid `GEMINI_API_KEY`:

```bash
python3 demo.py                    # Series 2.1 live
python3 series-2.2/app.py          # Series 2.2 live (one API call)
python3 series-2.3/app.py          # Series 2.3 live
# ... same pattern for 2.4, 2.5, 2.6
```

Each live run calls Gemini and prints real token counts plus an answer excerpt.

### Series 2.7 — Model Routing

```bash
python3 series-2.7/app.py --dry-run
python3 series-2.7/app.py --strategy confidence --dry-run
python3 series-2.7/app.py --request-id r0025 --dry-run
```

---

## Recommended lab order

```
2.1 Context Pruning          → send less evidence
2.2 Prompt Caching           → reuse stable instructions
2.3 RAG Chunking             → retrieve right chunks
2.4 Conversation Summarization → compress chat history
2.5 Long-Term Memory         → store durable facts
2.6 Memory Retrieval         → find the right memory at scale
2.7 Model Routing            → select the right model per request
```

---

## Troubleshooting

### `python3: command not found`

Use `python --version` instead, or install Python 3.10+ (see Step 2).

### `ModuleNotFoundError: No module named 'pandas'`

Activate the venv first: `source .venv/bin/activate`, then `pip install -r requirements.txt`.

### `... model ... is no longer available to new users`

Google periodically deprecates specific model IDs for newly-created API keys.
Add an override to `.env`:

```env
GEMINI_MODEL=gemini-flash-latest
```

`gemini-flash-latest` is a rolling alias Google maintains, so it won't go
stale the same way a pinned model version can.

### `Missing GEMINI_API_KEY in .env`

Either add the key to `.env`, or use `--dry-run` (no key needed).

### `Log file not found: datasets/HDFS_2k.log`

Run commands from the **repo root**, not from inside `series-2.1/`.

### Segfault or crash on import (macOS, some environments)

Use `--dry-run` — it skips loading the Gemini client. Dry-runs are the intended student path.

### Series 2.6 feels slow

Use `--memories 10000` for faster iteration; use default `100000` for the full benchmark.

### Notebook demo cell fails

Ensure the notebook kernel uses the same `.venv` where you ran `pip install -r requirements.txt`, or run from repo root so `demo.py` is found.

---

## Quick reference — daily use

After one-time setup, every session:

```bash
cd "/path/to/why-ai-fails"
source .venv/bin/activate          # skip if already active
python3 demo.py --dry-run          # or any series-2.x/app.py --dry-run
```

That is all you need for labs and presentations.

---

## Repository layout

```
why-ai-fails/
├── SETUP.md              ← This file
├── README.md             ← Lab overview
├── requirements.txt      ← Python dependencies
├── .env.example          ← API key template
├── demo.py               ← Series 2.1 entry point
├── common/               ← Shared Gemini client, token math, prompts
├── datasets/             ← HDFS_2k.log (Series 2.1 / 2.2)
├── docs/                 ← RAG corpus (Series 2.3)
├── series-2.1/ … series-2.6/   ← Engineering labs
```

---

## Support

- Lab READMEs: `series-2.x/README.md`
- Presentation notebooks: `Series_2.1` through `Series_2.8` under each `series-2.x/` folder
- Repo: https://github.com/sivadataanalytics/why-ai-fails
