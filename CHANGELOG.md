# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-05-16

### Added

- **CachedClient** (`src/caching.py`) — auto `cache_control` en system blocks >1024 tokens. Sync + async (`acreate`).
- **EvalPipeline** (`src/eval/pipeline.py`) — LLM-as-judge structured grade (score + strengths + weaknesses + reasoning).
- **HybridSearch** (`src/rag/hybrid.py`) — Voyage embeddings + BM25 lexical + RRF. Save/load index para persistencia.
- **BudgetGuard** (`src/budget.py`) — tracking costo por modelo + fail-fast en exceed.
- **MCP demo server** (`src/mcp_servers/demo.py`) — FastMCP con Tool + Resource direct/templated + Prompt.
- **Hooks**: PreToolUse `.env` block + PostToolUse type-check.
- **Skills**: commit-style, pr-review, code-audit.
- **Subagents**: researcher, reviewer, eval-grader.
- **Slash commands**: `/audit`, `/review`, `/eval`.
- **Anatomist-lint** (`scripts/anatomist-lint.py`) — 9 anti-pattern checks.
- **CI workflows**: anatomist-lint + eval-pipeline.
- **Pre-commit config** con ruff + anatomist-lint.
- **Demo end-to-end** (`examples/demo_chatbot.py`) — caching + RAG hybrid + eval combinados.
- **Sample data**: `src/eval/sample_dataset.json`, `src/rag/sample_corpus.md`.
- **Docs**: PATTERNS, DECISIONS, COST_MODEL, BEST_PRACTICES, EXTERNAL_VALIDATOR.
- **CLAUDE.md** con 10 north-star rules.

### Validation

- Tier1 tests: 6/6 passing.
- Anatomist-lint: 0 critical, 0 major, 0 minor.
- Python syntax: 6/6 core files clean.

### Source

Destilado de cursos Anthropic Skilljar (~10h video, 86 quizzes 100%):

- Claude Code 101
- Claude Code in Action
- Building with the Claude API
- Introduction to Agent Skills
- Introduction to Subagents
- Introduction to MCP
- MCP Advanced Topics
