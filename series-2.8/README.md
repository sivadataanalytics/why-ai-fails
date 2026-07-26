# Series 2.8 — Multi-Agent Orchestration

**Engineering Lab:** coordinate specialized AI agents through an orchestration layer — not one general-purpose agent.

> Enterprise AI systems scale through **coordination** rather than intelligence.

## What this demo proves

| Strategy | Approach | Tradeoff |
|----------|----------|----------|
| **Single** | One general agent handles everything | Fastest setup, incomplete domain coverage |
| **Sequential** | Planner → specialized agents in order | Higher quality, higher latency |
| **Parallel** | Independent agents run in parallel waves | Lower latency, shared memory consistency |
| **Parallel + Reviewer** | Parallel + validation + one rework iteration | Highest quality, small review overhead |

## Core principle

One intelligent agent can **answer**.

A coordinated team of specialized agents can **build**.

## Architecture

```
User Request
    ↓
Planner Agent → Task Decomposition
    ↓
Scheduler (sequential / parallel)
    ↓
Specialized Agents → Shared Memory
    ↓
Result Aggregator
    ↓
Reviewer Agent (reviewer strategy)
    ↓
Final Response
```

Agents **never communicate directly** — only through `SharedMemory`.

## Agent pool

| Agent | Responsibility |
|-------|----------------|
| Planner | Decompose request, dependencies |
| Architecture | System design, API boundaries |
| Backend | REST APIs, business logic |
| Frontend | UI components, screens |
| Database | Schema, indexes, SQL |
| Security | Auth, authorization, vulnerabilities |
| Testing | Unit and integration tests |
| DevOps | Docker, Kubernetes, CI/CD |
| Documentation | README, API docs |
| Reviewer | Consistency, gaps, final validation |

## Files

```
series-2.8/
  app.py              CLI entry — run benchmark
  tasks.py            500 enterprise requests (8 categories)
  agents.py           Specialized agent pool
  planner.py          Task decomposition
  scheduler.py        Sequential / parallel scheduling
  shared_memory.py    Shared context (read/write bus)
  orchestrator.py     Four orchestration strategies
  reviewer.py         Review + one rework iteration
  evaluator.py        Quality, consistency, completion metrics
  prompts.py          Live Gemini prompt templates
  benchmark.py        Side-by-side comparison printer
  README.md           This file
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # optional for live runs
```

## Run

```bash
# All four strategies — no API, $0
python series-2.8/app.py --dry-run

# Single strategy
python series-2.8/app.py --strategy reviewer --dry-run

# Inspect one request
python series-2.8/app.py --request-id r0024 --dry-run

# Smaller dataset (faster dev)
python series-2.8/app.py --requests 100 --dry-run

# Live Gemini (one request)
python series-2.8/app.py --request-id r0024
```

## CLI options

| Flag | Description |
|------|-------------|
| `--dry-run` | Simulate planning, scheduling, quality — no Gemini |
| `--strategy` | `single`, `sequential`, `parallel`, `reviewer` |
| `--request-id` | Inspect one request (e.g. `r0024`) |
| `--requests` | Dataset size (default: 500) |

## Benchmark metrics

| Metric | Description |
|--------|-------------|
| Prompt / Completion / Total Tokens | From `common/token_usage.py` |
| Latency | Simulated wall-clock (strategy-dependent) |
| Estimated Cost | Provider-neutral placeholder pricing |
| Task Completion | Required domains delivered |
| Consistency Score | Cross-agent output alignment |
| Security Score | Regulated-request security coverage |
| Review Score | Reviewer pass (reviewer strategy) |
| Overall Quality | Weighted composite |

## Expected observations

- **Single agent** — lowest task completion, moderate quality (~0.84)
- **Sequential** — full domain coverage, higher latency (~0.91 quality)
- **Parallel** — faster than sequential with same coverage (~0.92)
- **Parallel + Reviewer** — highest quality (~0.97), best enterprise recommendation

## Design choices

- **No LangChain / CrewAI / AutoGen** — plain Python orchestration
- **Reuses `common/`** — `gemini_client`, `token_usage`, `config`
- **Deterministic dry-run** — no API key required for full benchmark

## Previous labs

- [Series 2.7](../series-2.7/) — Model Routing
- [Series 2.6](../series-2.6/) — Memory Retrieval
- [Series 2.5](../series-2.5/) — Long-Term Memory

Series 2.8 completes the stack: after you prune, cache, retrieve, summarize, and route — **orchestrate** specialized agents to build complex systems.
