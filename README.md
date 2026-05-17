# anthropic-claude-starter

**Read this in:** **English** · [Español](README.es.md) · [中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/network/members)
[![Last commit](https://img.shields.io/github/last-commit/dc-holdings-spa/anthropic-claude-starter/main?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/commits/main)
[![Repo size](https://img.shields.io/github/repo-size/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg?style=flat)](https://github.com/astral-sh/ruff)
[![Built with Claude](https://img.shields.io/badge/built%20with-Claude-D97757?style=flat)](https://www.anthropic.com/claude)
[![Anthropic SDK](https://img.shields.io/pypi/v/anthropic?label=anthropic&style=flat)](https://pypi.org/project/anthropic/)
[![MCP SDK](https://img.shields.io/pypi/v/mcp?label=mcp&style=flat)](https://pypi.org/project/mcp/)

A production-grade starter template for building applications on top of the Anthropic Claude API, the Model Context Protocol (MCP), Skills, Subagents, and Hooks.

**Status:** v0.1.0 — production-grade, audited.

## Why this exists

Distilled from the official Anthropic Skilljar courses (~10h, ~86 quizzes completed at 100%) and practical experience building agentic systems in production. The goal is a clean baseline that ships the patterns that matter on day zero, with no scaffolding you have to delete later.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Stack](#stack)
- [Quick start](#quick-start)
- [Structure](#structure)
- [Patterns](#patterns)
- [Cost model](#cost-model)
- [Philosophy](#philosophy)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

An opinionated foundation for Claude-based applications. Wires together the Claude API client with automatic prompt caching, an MCP server scaffold, a deterministic eval pipeline, hybrid retrieval, hook-based guardrails, reusable skills and subagents, and a two-tier test harness. Designed for teams that want to build agentic systems without re-discovering the same patterns three sprints in.

## Features

| Component | Description |
|---|---|
| `CachedClient` | Anthropic API wrapper with automatic `cache_control` injection. Up to 90% discount on cached input tokens. |
| MCP server scaffold | FastMCP server template with Tool, templated Resource, and Prompt examples. |
| Eval pipeline | LLM-as-judge with structured output (score, strengths, weaknesses, reasoning). |
| Hybrid RAG | Voyage embeddings + BM25 lexical fused via Reciprocal Rank Fusion. No pure vector. |
| Hooks | `PreToolUse` `.env` access block. `PostToolUse` type-check on write. |
| Skills | `commit-style`, `pr-review`, `code-audit` scaffolds ready to extend. |
| Subagents | `researcher`, `reviewer`, `eval-grader` with structured output contracts. |
| `CLAUDE.md` | Ten north-star rules for LLM-first design, baked in. |
| `anatomist-lint` | Anti-pattern linter as pre-commit hook and CI gate. |
| Cost meter | Per-engagement budget tracking and reporting. |
| Two-tier eval | `tier1` deterministic (zero tokens). `tier2` token-burning regression. |
| External Validator Pattern | Doble Filo dual-LLM audit protocol, documented and ready to invoke. |

## Stack

| Dependency | Role |
|---|---|
| [`anthropic`](https://pypi.org/project/anthropic/) | Claude API SDK |
| [`mcp`](https://pypi.org/project/mcp/) | Model Context Protocol SDK |
| [`voyageai`](https://pypi.org/project/voyageai/) | Embedding model for hybrid retrieval |
| [`rank-bm25`](https://pypi.org/project/rank-bm25/) | Lexical retrieval component |
| [`fastapi`](https://pypi.org/project/fastapi/) | HTTP surface for the API scaffold |
| [`pytest`](https://pypi.org/project/pytest/) | Test runner for tier1 and tier2 |
| [`ruff`](https://pypi.org/project/ruff/) | Linter and formatter |

## Quick start

```bash
git clone https://github.com/dc-holdings-spa/anthropic-claude-starter my-app
cd my-app
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY. VOYAGE_API_KEY is optional (only needed for RAG).

# Initialise Claude settings (resolves $PWD into .claude/settings.local.json).
bash scripts/init-claude.sh

# Install and run the deterministic tier.
pip install -e .
pytest tests/tier1     # zero tokens
```

To run the token-burning regression suite:

```bash
pytest tests/tier2     # spends tokens; gated by CI label
```

## Structure

```
.claude/
├── settings.json            committed hooks, shared with the team
├── settings.local.json      gitignored, generated by init-claude.sh
├── skills/                  shared skills
├── agents/                  custom subagents
└── commands/                slash commands

src/
├── api/                     FastAPI server scaffold
├── prompts/                 versioned prompts, linked to evals
├── tools/                   custom tool functions
├── mcp_servers/             FastMCP servers
├── eval/                    eval pipeline framework
├── rag/                     hybrid retrieval (vector + BM25 + RRF)
└── caching.py               Claude client with cache_control auto-injection

tests/
├── tier1/                   deterministic, zero tokens, make e2e
└── tier2/                   burns tokens, make e2e-full

scripts/
├── init-claude.sh           $PWD resolver
└── anatomist-lint.py        anti-pattern check

docs/
├── PATTERNS.md              decision tree and cheat sheet
├── DECISIONS.md             workflow vs agent decisions
├── COST_MODEL.md            estimation framework
├── BEST_PRACTICES.md        cross-course synthesis
└── EXTERNAL_VALIDATOR.md    Doble Filo protocol

.github/workflows/
├── anatomist-lint.yml       CI gate for anti-patterns
└── eval-pipeline.yml        runs evals on every PR
```

## Patterns

A decision tree for choosing the right Claude primitive.

| Need | Use | Reference |
|---|---|---|
| Knowledge that is always relevant | `CLAUDE.md` | [docs/PATTERNS.md](docs/PATTERNS.md) |
| Knowledge that is task-specific | Skill | [.claude/skills/](.claude/skills/) |
| React to events automatically | Hook | [.claude/settings.json](.claude/settings.json) |
| Task that needs isolated context | Subagent | [.claude/agents/](.claude/agents/) |
| External service or data source | MCP server | [src/mcp_servers/](src/mcp_servers/) |
| Programmatic Claude Code | `@anthropic-ai/claude-agent-sdk` | [docs/PATTERNS.md](docs/PATTERNS.md) |

## Cost model

Order-of-magnitude targets for typical workloads.

| Workload | Target cost |
|---|---|
| Single API request (basic prompt) | $0.002 – $0.01 |
| Engagement with eval pipeline and caching | $0.10 – $0.50 |
| End-to-end client POC | $5 – $15 |

Full methodology in [docs/COST_MODEL.md](docs/COST_MODEL.md).

## Philosophy

1. Solve problems reliably before designing elegant architectures.
2. Determinism beats hope. Use hooks instead of prompts for critical paths.
3. The context window is finite. Protect it with subagents for exploration.
4. Stateless by default. Stateful only with an explicit, measured cost.
5. Structured output beats nicely-worded prompts.
6. Tool descriptions do two jobs: when to call, and how to call.
7. Least privilege on tools. Allow-list per agent.
8. Verification costs less than trust. `PreToolUse` hooks and citations are cheap.

## Contributing

Issues and pull requests are welcome. Before opening a PR:

1. Run `ruff format` and `ruff check`.
2. Run `pytest tests/tier1`. Must pass with zero tokens.
3. Run `python scripts/anatomist-lint.py`. Must pass.
4. If you touch prompts or eval logic, run `pytest tests/tier2` and attach the report.

## License

MIT. See [LICENSE](LICENSE).
