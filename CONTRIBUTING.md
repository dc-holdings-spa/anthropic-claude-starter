# Contributing

## Setup

```bash
git clone <repo> && cd anthropic-claude-starter
cp .env.example .env  # editar con tus keys
make install
make init             # resuelve $PWD en hooks
make e2e              # tier1 tests, cero tokens
```

## Workflow

1. Branch desde `main`: `git checkout -b feat/<slug>`
2. Implementa con tests tier1
3. Pre-commit corre auto (ruff + anatomist-lint)
4. PR a `main` — CI gate bloquea si anti-pattern findings
5. Review checklist en `.claude/skills/pr-review/SKILL.md`

## Estándares

- **Tests tier1 obligatorios** para cada feature nueva
- **Anatomist-lint clean** antes de commit
- **CLAUDE.md rules respetadas** (LLM-first, no substring classifiers, etc)
- **Commits Conventional**: `feat(scope): subject` formato

## Anti-patterns bloqueantes (CI fails si presentes)

- API key hardcoded
- Substring/regex classifiers para contenido semántico
- Hooks con path relativo
- Tool descriptions vagas (<20 chars) o duplicadas
- Test runner subagents sin output completo

Ver `docs/BEST_PRACTICES.md` para lista completa.

## Estructura aporte típico

```
src/<feature>/
├── __init__.py
├── <feature>.py        ← implementación
tests/tier1/
└── test_<feature>.py   ← deterministic
docs/                   ← actualizar PATTERNS.md si nuevo pattern
```

## Para añadir nuevo Skill / Subagent / MCP server

- Skill: `.claude/skills/<name>/SKILL.md` con frontmatter (name + description)
- Subagent: `.claude/agents/<name>.md` con frontmatter (name + description + tools + model + color)
- MCP server: `src/mcp_servers/<name>.py` con FastMCP + test via `mcp dev`

## External Validator Pattern

Para merges high-stakes (>500 LOC, security, refactor cross-cutting):
- Ver `docs/EXTERNAL_VALIDATOR.md` para protocolo Doble Filo
- 2 chats independientes, operador brokerea

## License

MIT — ver `LICENSE`.
