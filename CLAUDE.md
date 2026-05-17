# Project — Anthropic Claude App

This file is loaded into every Claude Code session. Binding contract between operator and assistant.

## North star

This app uses Claude API + MCP + Skills + Hooks. Build patterns:

1. **LLM-first**: domain decisions are model calls with context — never hardcoded Python `if/else`.
2. **Eval-driven**: prompts pass eval pipeline before deploy. No "tested once, shipped".
3. **Cost-disciplined**: prompt caching obligatorio en system prompts >1024 tokens. Haiku para bulk tasks.
4. **Audit-ready**: every risky tool call flows through structured logging.
5. **Citations enabled** cuando user verifies info de documentos.

## The 10 rules

1. **LLM takes domain decisions**. Routing, classification, risk scoring = model calls.
2. **Python is plumbing**. I/O wrappers, parsing, glue code only. No semantic classifiers.
3. **Every agent thought → structured log**. Audit trail obligatorio.
4. **Zero regex/substring classifiers for semantic content**.
5. **Tools return facts, not decisions**.
6. **Skills follow standard pattern**: SKILL.md frontmatter + body. NO Python `handle()` con domain logic.
7. **Primary delegation via tool calls**. No Python dispatch tables.
8. **Output structured format** en subagents (numbered sections + obstacles).
9. **Threshold + LLM mentor para anti-loop**. Counters detect cheap, LLM judges.
10. **HITL gates obligatorios** para risky actions.

## Anti-patterns prohibidos

- ❌ Tested-once deployed (use eval pipeline)
- ❌ API key en frontend (backend-only, siempre)
- ❌ Mega-prompt con todas las reglas (use chaining/routing/parallelization)
- ❌ Expert claim subagents ("you are X expert")
- ❌ Sequential pipelines con dependencia entre pasos
- ❌ Test runner subagents que esconden output
- ❌ Path relativo en hook commands (T1574.007 risk)
- ❌ Descriptions similares entre skills/subagents/MCPs
- ❌ Tool allowlist > N tools sin justificación (least-privilege)

## Style rules

- **Honesty over diplomacy**. Name violations con file:line refs.
- **Evidence over opinion**. Every claim verifiable con grep/cat.
- **E2E before DoD**. No feature "done" sin test que exercise el path.
- **Feature flags para risky changes**. Rollback ready.
- **No backwards-compatibility shims** unless explicitly asked.
- **Terse responses**. Operator reads diff. Summaries 1-2 sentences.

## Default workflow

1. **Explore**: read code, understand context
2. **Plan**: `/plan` mode antes de editar (Shift+Tab×2)
3. **Code**: implement con tests tier1
4. **Eval**: run `tests/tier1/` cero tokens
5. **Commit**: Conventional Commits format

## Cost discipline

- Prompt caching: usar `cache_control` en system prompts large
- Haiku 4.5: para eval grading + dataset gen + batch
- Sonnet 4.5: para main reasoning
- Opus 4.7: para orchestration cuando justifica

Budget alert si engagement > $15 USD.

## References

- [docs/PATTERNS.md](docs/PATTERNS.md) — decision tree + cheat sheet
- [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) — cross-curso síntesis
- [docs/EXTERNAL_VALIDATOR.md](docs/EXTERNAL_VALIDATOR.md) — Doble Filo
- [docs/COST_MODEL.md](docs/COST_MODEL.md) — estimation
