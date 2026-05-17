# Best Practices — Síntesis Anthropic

Destilado de cursos Skilljar (Claude Code 101, Claude Code in Action, Building with the Claude API, Intro to Agent Skills, Intro to Subagents, Intro to MCP, MCP Advanced Topics).

## 8 principios core

1. **Resolver problemas confiablemente > arquitectura elegante**
2. **Determinismo > esperanza** (hooks > prompts para critical paths)
3. **Context window es finito — protégelo** (subagents, lazy loading, compact agresivo)
4. **Stateless es default, stateful tiene costo**
5. **Output estructurado > prompt nice** (mata middle bias en LLM-as-judge)
6. **Tool descriptions hacen DOS cosas**: cuándo invocar + cómo escribir input prompt
7. **Least-privilege en tools** (allow-list explícito)
8. **Verificación cuesta menos que confianza** (hooks PreToolUse, citations enabled, eval pipeline)

## 10 patterns que sí aplicar

1. Prefill + stop_sequences para output JSON puro
2. Multi-turn loop con `stop_reason="tool_use"`
3. LLM-as-judge con score + strengths + weaknesses + reasoning
4. Progressive disclosure (skills/playbooks con references lazy)
5. Scripts run-not-read (output-only en contexto, no contenido del script)
6. Hooks deterministas para file operations críticas
7. Prompt caching en system prompts >1024 tokens (90% off)
8. Subagent structured output + obstacle reporting
9. MCP server custom + Inspector pre-Claude
10. Routing workflow para multi-genre tasks

## 10 anti-patterns evitar

1. Tested-once, deployed (use eval pipeline)
2. Sequential subagent pipelines con dependencia (info loss handoff)
3. Test runner subagent (esconde output crítico)
4. "Expert claim" subagents (cero value, Claude ya tiene knowledge)
5. Mega-prompt con todas las reglas (use routing/parallelization)
6. API key en frontend (siempre backend)
7. `temperature=0` para creative tasks
8. Nueva sesión por request (no aprovecha historial cacheable)
9. Path relativo en hook commands (T1574.007)
10. Descriptions similares entre tools/skills/agents

## Decision: feature usar cuándo

| Necesidad | Feature |
|-----------|---------|
| Conocimiento siempre aplicable | CLAUDE.md |
| Conocimiento task-specific | Skill |
| Reacción a eventos automático | Hook |
| Tarea con contexto aislado | Subagent |
| Servicio externo | MCP server |
| Embedded Claude Code | Claude Agent SDK |

## Workflow patterns (5)

1. **Chaining** — pasos secuenciales conocidos
2. **Routing** — clasificar + dispatch por categoría
3. **Parallelization** — sub-tasks independientes + consolidate
4. **Orchestrator-workers** — Claude principal delega + sintetiza
5. **Evaluator-optimizer** — generar → evaluar → mejorar loop

## MCP primitives

| Primitive | Quién controla | Para qué |
|-----------|----------------|----------|
| Tools | Model decide | Acciones |
| Resources | User fetch | Data read-only |
| Prompts | User invoca | Templates pre-testeadas |

## MCP transports

| Transport | Cuándo |
|-----------|--------|
| stdio | Local, misma máquina, stdin/stdout |
| StreamableHTTP | Remoto, HTTP + SSE para server-initiated msgs |

## MCP advanced features

- **Sampling** — server pide al cliente que ejecute LLM (server no necesita API key)
- **Roots** — filesystem paths que user pre-aprueba al server
- **Progress notifications** — server emite updates one-way
- **Log notifications** — debug/info/warning/error structured

## Skill priority (top to bottom)

1. Enterprise (managed settings)
2. Personal (`~/.claude/skills/`)
3. Project (`.claude/skills/`)
4. Plugin

Mismo `name` → mayor prioridad gana. Usar nombres descriptivos para evitar collision.

## Cost optimization

- Prompt caching en system prompts grandes → 90% off
- Haiku para bulk (eval grading, dataset gen, simple tasks)
- Sonnet para main reasoning
- Opus solo para orchestration multi-step compleja
- Scripts run-not-read → output-only consume contexto
- Subagent para research → main context no pollutes
- Streaming → UX percibida solo, NO ahorro de costo

## Eval workflow (5 steps)

1. **Dataset** — curado o LLM-as-generator (Haiku)
2. **Run prompt** — sobre cada test case
3. **Grade** — code-based (objetivo) o model-based (subjetivo)
4. **Aggregate** — avg + distribución
5. **Iterate** — mejorar prompt, re-run, comparar

Sin esto = "tested once, deployed" = trampa donde caen ingenieros.

## Production checklist

### Security
- [ ] API key solo backend
- [ ] `.env` en `.gitignore`
- [ ] Hooks PreToolUse para archivos sensitive
- [ ] `allowed-tools` whitelist explícito
- [ ] Absolute paths en hooks
- [ ] `permissions.deny` para paths críticos

### Performance + costo
- [ ] Prompt caching habilitado
- [ ] Haiku para tareas masivas
- [ ] Streaming para UX
- [ ] `max_tokens` cap razonable
- [ ] Budget guard por engagement

### Calidad
- [ ] Eval pipeline pre-deploy
- [ ] LLM-as-judge structured grade
- [ ] Output structured en subagents
- [ ] Citations enabled si user verifica
- [ ] Runnable examples (no pseudo-code)

### Maintenance
- [ ] CLAUDE.md commit
- [ ] `.claude/{skills,agents,settings}` commit
- [ ] `settings.local.json` en gitignore
- [ ] Subagent skills explícito en frontmatter
- [ ] MCP servers documentados + inspector test

### Observability
- [ ] Hooks PostToolUse para logging
- [ ] Métricas tokens + latency
- [ ] Audit trail tipo `audit trail event log`
- [ ] Obstacle reports surfaced
- [ ] Error mode catalog

## Referencias cursos originales

- Claude Code 101 — fundamentos CLI
- Claude Code in Action — práctica hooks + SDK + GitHub
- Building with the Claude API — API directa + features
- Intro to Agent Skills — skills standalone
- Intro to Subagents — subagents deep
- Intro to MCP — MCP fundamentos
- MCP Advanced Topics — sampling + roots + transports

Total: ~10h video + 86 quizzes pasados 100%.
