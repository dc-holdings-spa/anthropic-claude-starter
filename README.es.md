# anthropic-claude-starter

**Léelo en:** [English](README.md) · **Español** · [中文](README.zh-CN.md)

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

Plantilla starter de grado productivo para construir aplicaciones sobre la API de Anthropic Claude, el Model Context Protocol (MCP), Skills, Subagents y Hooks.

**Estado:** v0.1.0 — grado productivo, auditado.

## Por qué existe

Destilado desde los cursos oficiales de Anthropic Skilljar (~10h, ~86 quizzes completados al 100%) y experiencia práctica construyendo sistemas agénticos en producción. La meta es una base limpia que entrega los patrones que importan desde el día cero, sin scaffolding que después tengas que borrar.

---

## Tabla de contenidos

- [Visión general](#visión-general)
- [Características](#características)
- [Stack](#stack)
- [Inicio rápido](#inicio-rápido)
- [Estructura](#estructura)
- [Patrones](#patrones)
- [Modelo de costo](#modelo-de-costo)
- [Filosofía](#filosofía)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Visión general

Una base opinada para aplicaciones basadas en Claude. Cablea el cliente API de Claude con prompt caching automático, un scaffold de servidor MCP, un pipeline de evals determinista, retrieval híbrido, guardrails basados en hooks, skills y subagents reutilizables, y un test harness de dos niveles. Diseñada para equipos que quieren construir sistemas agénticos sin re-descubrir los mismos patrones tres sprints después.

## Características

| Componente | Descripción |
|---|---|
| `CachedClient` | Wrapper de la API de Anthropic con inyección automática de `cache_control`. Hasta 90% de descuento en input tokens cacheados. |
| Scaffold servidor MCP | Plantilla de servidor FastMCP con ejemplos de Tool, Resource templated y Prompt. |
| Pipeline eval | LLM-as-judge con structured output (score, fortalezas, debilidades, razonamiento). |
| RAG híbrido | Embeddings de Voyage + BM25 léxico fusionados vía Reciprocal Rank Fusion. Sin vector puro. |
| Hooks | `PreToolUse` bloquea acceso a `.env`. `PostToolUse` type-check al escribir. |
| Skills | Scaffolds `commit-style`, `pr-review`, `code-audit` listos para extender. |
| Subagents | `researcher`, `reviewer`, `eval-grader` con contratos de structured output. |
| `CLAUDE.md` | Diez reglas norte para diseño LLM-first, integradas. |
| `anatomist-lint` | Linter de anti-patterns como pre-commit hook y gate de CI. |
| Medidor de costos | Tracking de budget y reporte por engagement. |
| Eval de dos niveles | `tier1` determinista (cero tokens). `tier2` regresión que quema tokens. |
| Patrón External Validator | Protocolo Doble Filo de auditoría dual-LLM, documentado y listo para invocar. |

## Stack

| Dependencia | Rol |
|---|---|
| [`anthropic`](https://pypi.org/project/anthropic/) | SDK de la API de Claude |
| [`mcp`](https://pypi.org/project/mcp/) | SDK del Model Context Protocol |
| [`voyageai`](https://pypi.org/project/voyageai/) | Modelo de embeddings para retrieval híbrido |
| [`rank-bm25`](https://pypi.org/project/rank-bm25/) | Componente de retrieval léxico |
| [`fastapi`](https://pypi.org/project/fastapi/) | Superficie HTTP para el scaffold de API |
| [`pytest`](https://pypi.org/project/pytest/) | Test runner para tier1 y tier2 |
| [`ruff`](https://pypi.org/project/ruff/) | Linter y formateador |

## Inicio rápido

```bash
git clone https://github.com/dc-holdings-spa/anthropic-claude-starter my-app
cd my-app
cp .env.example .env
# Edita .env: setea ANTHROPIC_API_KEY. VOYAGE_API_KEY es opcional (solo para RAG).

# Inicializa los settings de Claude (resuelve $PWD en .claude/settings.local.json).
bash scripts/init-claude.sh

# Instala y corre el tier determinista.
pip install -e .
pytest tests/tier1     # cero tokens
```

Para correr la suite de regresión que quema tokens:

```bash
pytest tests/tier2     # gasta tokens; gated por label de CI
```

## Estructura

```
.claude/
├── settings.json            hooks commiteados, compartidos con el equipo
├── settings.local.json      gitignored, generado por init-claude.sh
├── skills/                  skills compartidas
├── agents/                  subagents custom
└── commands/                slash commands

src/
├── api/                     scaffold de servidor FastAPI
├── prompts/                 prompts versionados, ligados a evals
├── tools/                   funciones de tools custom
├── mcp_servers/             servidores FastMCP
├── eval/                    framework del pipeline de evals
├── rag/                     retrieval híbrido (vector + BM25 + RRF)
└── caching.py               cliente Claude con auto-inyección de cache_control

tests/
├── tier1/                   determinista, cero tokens, make e2e
└── tier2/                   quema tokens, make e2e-full

scripts/
├── init-claude.sh           resolvedor de $PWD
└── anatomist-lint.py        check de anti-patterns

docs/
├── PATTERNS.md              árbol de decisión y cheat sheet
├── DECISIONS.md             decisiones workflow vs agent
├── COST_MODEL.md            framework de estimación
├── BEST_PRACTICES.md        síntesis cruzada de cursos
└── EXTERNAL_VALIDATOR.md    protocolo Doble Filo

.github/workflows/
├── anatomist-lint.yml       gate de CI para anti-patterns
└── eval-pipeline.yml        corre evals en cada PR
```

## Patrones

Un árbol de decisión para elegir la primitiva correcta de Claude.

| Necesidad | Usa | Referencia |
|---|---|---|
| Conocimiento siempre relevante | `CLAUDE.md` | [docs/PATTERNS.md](docs/PATTERNS.md) |
| Conocimiento específico de tarea | Skill | [.claude/skills/](.claude/skills/) |
| Reaccionar a eventos automáticamente | Hook | [.claude/settings.json](.claude/settings.json) |
| Tarea que necesita contexto aislado | Subagent | [.claude/agents/](.claude/agents/) |
| Servicio o fuente de datos externo | Servidor MCP | [src/mcp_servers/](src/mcp_servers/) |
| Claude Code programático | `@anthropic-ai/claude-agent-sdk` | [docs/PATTERNS.md](docs/PATTERNS.md) |

## Modelo de costo

Objetivos de orden de magnitud para workloads típicos.

| Workload | Costo objetivo |
|---|---|
| Solicitud API única (prompt básico) | $0.002 – $0.01 |
| Engagement con pipeline de eval y caching | $0.10 – $0.50 |
| POC cliente end-to-end | $5 – $15 |

Metodología completa en [docs/COST_MODEL.md](docs/COST_MODEL.md).

## Filosofía

1. Resolver problemas confiablemente antes de diseñar arquitecturas elegantes.
2. Determinismo le gana a la esperanza. Usa hooks en vez de prompts para rutas críticas.
3. La ventana de contexto es finita. Protégela con subagents para exploración.
4. Stateless por defecto. Stateful solo con costo explícito y medido.
5. Structured output le gana a prompts bien redactados.
6. Las descripciones de tools hacen dos trabajos: cuándo llamar, y cómo llamar.
7. Privilegio mínimo en tools. Allow-list por agent.
8. Verificar cuesta menos que confiar. Los hooks `PreToolUse` y las citations son baratos.

## Contribuir

Issues y pull requests son bienvenidos. Antes de abrir un PR:

1. Corre `ruff format` y `ruff check`.
2. Corre `pytest tests/tier1`. Debe pasar con cero tokens.
3. Corre `python scripts/anatomist-lint.py`. Debe pasar.
4. Si tocas prompts o lógica de eval, corre `pytest tests/tier2` y adjunta el reporte.

## Licencia

MIT. Ver [LICENSE](LICENSE).
