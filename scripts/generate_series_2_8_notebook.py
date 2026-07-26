#!/usr/bin/env python3
"""Generate Series 2.8 presentation notebook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from add_python_file_sections import patch_notebook  # noqa: E402
from fix_notebook_format import to_source_list  # noqa: E402

DEMO_CELL = """# Live demo cell — run the dry-run benchmark ($0, no API key needed)
import subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "demo.py").exists() and (ROOT.parent / "demo.py").exists():
    ROOT = ROOT.parent

result = subprocess.run(
    [sys.executable, str(ROOT / "series-2.8/app.py"), "--dry-run", "--requests", "50"],
    cwd=str(ROOT), capture_output=True, text=True,
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
print(f"\\nExit code: {result.returncode}")
"""

CELLS = [
    (
        "# Series 2.8 — Multi-Agent Orchestration\n\n"
        "**Why AI Fails? — Engineering Lab**\n\n"
        "---\n\n"
        "> Enterprise AI systems scale through **coordination** rather than intelligence.\n\n"
        "**Scenario:** 500 enterprise software build requests — four orchestration strategies, "
        "ten specialized agents, shared memory bus.\n\n"
        "**Core lesson:** One agent can answer. A coordinated team of specialized agents can **build**."
    ),
    (
        "## 1. The Problem\n\n"
        "| Single general agent | Multi-agent orchestration |\n"
        "|----------------------|---------------------------|\n"
        "| One prompt, one response | Planner decomposes into domain tasks |\n"
        "| Shallow coverage of architecture, security, tests | Each domain gets a specialist |\n"
        "| No dependency management | Scheduler runs sequential or parallel waves |\n"
        "| Agents talk through prompt bloat | Agents communicate via **Shared Memory** only |\n"
        "| No quality gate | Reviewer validates + one rework iteration |\n\n"
        "**Expected dry-run results:**\n\n"
        "```\n"
        "SINGLE AGENT         →  ~18s latency, quality ~0.84, 50% task completion\n"
        "SEQUENTIAL           →  ~14s latency, quality ~0.91, full completion\n"
        "PARALLEL             →  ~8s latency, quality ~0.92, full completion\n"
        "PARALLEL + REVIEWER  →  ~10s latency, quality ~0.97, enterprise pick\n"
        "```"
    ),
    (
        "## 2. What is Multi-Agent Orchestration?\n\n"
        "**Multi-agent orchestration** coordinates **specialized AI agents** through a central "
        "orchestration layer to solve complex enterprise tasks.\n\n"
        "### Definition\n\n"
        "```\n"
        "Orchestration = request → planner → scheduler → agents → shared memory\n"
        "                → aggregator → (reviewer) → final response\n"
        "```\n\n"
        "### Key principle\n\n"
        "Agents **never communicate directly**. They read and write **Shared Memory** only.\n\n"
        "### Agent pool\n\n"
        "| Agent | Domain |\n"
        "|-------|--------|\n"
        "| Planner | Task decomposition, dependencies |\n"
        "| Architecture | System design, API boundaries |\n"
        "| Backend | REST APIs, business logic |\n"
        "| Frontend | UI components |\n"
        "| Database | Schema, indexes, SQL |\n"
        "| Security | Auth, authorization, vulnerabilities |\n"
        "| Testing | Unit + integration tests |\n"
        "| DevOps | Docker, Kubernetes, CI/CD |\n"
        "| Documentation | README, API docs |\n"
        "| Reviewer | Consistency, gaps, validation |\n\n"
        "### Four strategies\n\n"
        "| Strategy | CLI | Behavior |\n"
        "|----------|-----|----------|\n"
        "| Single | `--strategy single` | One general agent (baseline) |\n"
        "| Sequential | `--strategy sequential` | Agents run in dependency order |\n"
        "| Parallel | `--strategy parallel` | Independent agents in parallel waves |\n"
        "| Reviewer | `--strategy reviewer` | Parallel + review + one rework pass |"
    ),
    (
        "## 3. Repository Layout\n\n"
        "```\n"
        "why-ai-fails/\n"
        "├── common/                        ← Gemini client, token math\n"
        "└── series-2.8/\n"
        "    ├── app.py                     ← CLI + benchmark runner\n"
        "    ├── tasks.py                   ← 500 enterprise requests\n"
        "    ├── agents.py                  ← Specialized agent pool\n"
        "    ├── planner.py                 ← Task decomposition\n"
        "    ├── scheduler.py               ← Sequential / parallel waves\n"
        "    ├── shared_memory.py           ← Shared context bus\n"
        "    ├── orchestrator.py            ← Four strategies\n"
        "    ├── reviewer.py                ← Review + rework\n"
        "    ├── evaluator.py               ← Quality metrics\n"
        "    ├── benchmark.py               ← Comparison printer\n"
        "    ├── README.md\n"
        "    └── Series_2.8_Multi_Agent_Orchestration.ipynb   ← This notebook\n"
        "```"
    ),
    # Section 4 inserted by patch_notebook (Python Files)
    (
        "## 4. The Orchestration Pipeline (`orchestrator.py`)\n\n"
        "```\n"
        "User Request\n"
        "    ↓\n"
        "Planner Agent → Task Decomposition\n"
        "    ↓\n"
        "Scheduler (sequential or parallel waves)\n"
        "    ↓\n"
        "Specialized Agents (read/write Shared Memory)\n"
        "    ↓\n"
        "Result Aggregator\n"
        "    ↓\n"
        "Reviewer Agent (reviewer strategy only)\n"
        "    ↓\n"
        "Final Response\n"
        "```\n\n"
        "**Example task graph** for \"Build a production-ready banking application\":\n\n"
        "```\n"
        "Architecture → Database → Backend → Frontend\n"
        "                    ↘         ↓\n"
        "                  Security  Testing → DevOps → Documentation\n"
        "```"
    ),
    (
        "## 5. Three Layers of Orchestration Engineering\n\n"
        "### Layer 1 — Plan and schedule (decompose before executing)\n\n"
        "The **Planner** breaks one enterprise request into dependent tasks. "
        "The **Scheduler** orders them sequentially or groups parallel waves.\n\n"
        "---\n\n"
        "### Layer 2 — Coordinate through Shared Memory\n\n"
        "Every agent reads prior outputs from shared memory and writes its deliverable. "
        "No direct agent-to-agent messages — prevents inconsistent handoffs.\n\n"
        "Memory keys: `architecture`, `database`, `backend`, `frontend`, `security`, "
        "`testing`, `devops`, `documentation`, `review`\n\n"
        "---\n\n"
        "### Layer 3 — Measure quality per unit time\n\n"
        "| Metric | What it tells you |\n"
        "|--------|-------------------|\n"
        "| **Task Completion** | Required domains delivered |\n"
        "| **Consistency Score** | Cross-agent alignment |\n"
        "| **Security Score** | Regulated-request coverage |\n"
        "| **Review Score** | Reviewer pass quality |\n"
        "| **Overall Quality** | Weighted composite |\n"
        "| **Latency** | Sequential vs parallel tradeoff |\n\n"
        "| Mode | Flag | API key? |\n"
        "|------|------|----------|\n"
        "| **Dry-run** | `--dry-run` | No — **$0** |\n"
        "| **Live** | (none) | Yes — one request demo |"
    ),
    (
        "## 6. Execution Flow\n\n"
        "```\n"
        "Parse CLI (--strategy, --request-id, --requests)\n"
        "    │\n"
        "    └─ For each request + strategy:\n"
        "            planner.decompose_request()\n"
        "            scheduler.schedule(waves)\n"
        "            agents execute → shared_memory.write()\n"
        "            memory.aggregate()\n"
        "            reviewer.review() (reviewer strategy)\n"
        "            evaluator score\n"
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
        "| `python series-2.8/app.py --dry-run` | All four strategies, 500 requests | No |\n"
        "| `python series-2.8/app.py --strategy reviewer --dry-run` | Best strategy | No |\n"
        "| `python series-2.8/app.py --request-id r0024 --dry-run` | Inspect one request | No |\n"
        "| `python series-2.8/app.py --requests 100 --dry-run` | Faster dev test | No |\n"
        "| `python series-2.8/app.py --request-id r0024` | Live Gemini | Yes |"
    ),
    (
        "## 8. Key Code Snippets\n\n"
        "### Shared Memory (`shared_memory.py`)\n\n"
        "```python\n"
        "class SharedMemory:\n"
        "    def read(self, key=None): ...\n"
        "    def write(self, key, value, *, agent_id): ...\n"
        "    def write_agent_output(self, agent_result): ...\n"
        "    def aggregate(self) -> str: ...\n"
        "```\n\n"
        "### Orchestrator strategies\n\n"
        "```python\n"
        "STRATEGIES = (\"single\", \"sequential\", \"parallel\", \"reviewer\")\n"
        "\n"
        "def orchestrate(request, strategy, *, dry_run=True):\n"
        "    ...\n"
        "```"
    ),
    (
        "## 9. Where Series 2.8 Fits\n\n"
        "Series 2.8 **completes the enterprise AI stack**:\n\n"
        "| Lab | Layer |\n"
        "|-----|-------|\n"
        "| 2.1 | Prune evidence |\n"
        "| 2.2 | Cache stable prompts |\n"
        "| 2.3–2.6 | Retrieve & remember |\n"
        "| 2.7 | Route to the right model |\n"
        "| **2.8** | **Orchestrate specialized agents** |\n\n"
        "---\n\n"
        "## Takeaway\n\n"
        "> **Enterprise AI systems do not scale because they create more agents. "
        "They scale because they orchestrate them intelligently.**\n\n"
        "**Previous lab:** [Series 2.7 — Model Routing](../series-2.7/)"
    ),
]

def main() -> None:
    path = ROOT / "series-2.8/Series_2.8_Multi_Agent_Orchestration.ipynb"
    cells = []
    how_to_run_idx = 7  # insert demo after "How to Run" markdown cell
    for i, source in enumerate(CELLS):
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": to_source_list(source),
            "id": f"cell-{i:02d}",
        })
        if i == how_to_run_idx:
            cells.append({
                "cell_type": "code",
                "metadata": {},
                "source": to_source_list(DEMO_CELL),
                "execution_count": None,
                "outputs": [],
                "id": "demo-cell",
            })
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    patch_notebook("series-2.8", path)
    print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
