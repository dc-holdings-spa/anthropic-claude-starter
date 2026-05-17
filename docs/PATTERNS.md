# Patterns — Cheat sheet

Decision tree + patterns ready-to-apply. Destilado de cursos Anthropic Skilljar.

## Decision tree: qué feature usar

```
¿Qué necesito?
│
├── Conocimiento que SIEMPRE aplica
│   └── CLAUDE.md (always-on, single global context)
│
├── Conocimiento que aplica A VECES (task-specific)
│   └── Skill (semantic match, lazy load, .claude/skills/)
│
├── Reaccionar a EVENTOS automático
│   └── Hook (.claude/settings.json)
│       ├── Pre/PostToolUse — bloquear/formatear
│       ├── Stop — notificar
│       └── UserPromptSubmit — inyectar contexto
│
├── Delegar tarea con CONTEXTO AISLADO
│   └── Subagent (.claude/agents/)
│       ├── ¿intermediate work matters? → NO → subagent
│       │                              → SÍ → main thread
│       └── Custom system prompt distinto → siempre subagent
│
├── Acceso a SERVICIO EXTERNO
│   └── MCP server
│       ├── Tool (model decide, ejecuta acción)
│       ├── Resource (user fetch, expone data, URI templated)
│       └── Prompt (user invoca, template pre-testeada)
│
└── Programmatic Claude Code embebido
    └── Claude Agent SDK (@anthropic-ai/claude-agent-sdk)
```

## Workflow vs Agent

| | Workflow | Agent |
|---|---|---|
| ¿Conozco los pasos? | sí | no |
| Predictibilidad | alta | baja |
| Testeable | sí | no |
| Success rate | alto | bajo |
| Recomendación | **default** | fallback |

## 5 workflow patterns

1. **Chaining** — pasos secuenciales, output → input siguiente
2. **Routing** — clasificar primero + dispatch a sub-workflow
3. **Parallelization** — sub-tasks independientes paralelo + consolidate
4. **Orchestrator-workers** — Claude principal delega + sintetiza
5. **Evaluator-optimizer** — generar → evaluar → mejorar (loop)

## Top patterns ready-to-copy

### 1. Structured JSON output (prefill + stop)

```python
client.messages.create(
    messages=[
        {"role": "user", "content": "Extract X as JSON"},
        {"role": "assistant", "content": "```json\n"}
    ],
    stop_sequences=["```"]
)
```

### 2. Tool use loop

```python
while r.stop_reason == "tool_use":
    tool_block = next(b for b in r.content if b.type == "tool_use")
    result = execute_tool(tool_block.name, tool_block.input)
    messages.append({"role": "assistant", "content": r.content})
    messages.append({"role": "user", "content": [{
        "type": "tool_result",
        "tool_use_id": tool_block.id,
        "content": str(result)
    }]})
    r = client.messages.create(...)
```

### 3. LLM-as-judge structured

```python
eval_prompt = """Rate 1-5. JSON only:
{"score", "strengths", "weaknesses", "reasoning"}"""
# Pedir todos los campos = mata middle bias
```

### 4. Prompt caching (90% off)

```python
system=[
    {"type": "text", "text": short_persona},
    {"type": "text", "text": LARGE_CONTEXT,
     "cache_control": {"type": "ephemeral"}}   # ← breakpoint
]
```

### 5. Progressive disclosure (Skills)

```
my-skill/
├── SKILL.md           ← lean (<500 LOC)
├── references/        ← lazy load
└── scripts/           ← run-not-read (output-only tokens)
```

### 6. Hook PreToolUse blocking

```js
if (toolInput.file_path.includes(".env")) {
    console.error("Cannot read .env");
    process.exit(2);   // ← stderr feedback a Claude
}
```

### 7. MCP server FastMCP

```python
mcp = FastMCP("my-server")

@mcp.tool()
def my_action(arg: str) -> str:
    """Descripción que Claude usa para matching."""
    return result

@mcp.resource("data://items/{id}")
def fetch(id: str) -> str: ...

@mcp.prompt()
def template(arg: str) -> str: ...
```

### 8. Subagent con structured output

Frontmatter:
```yaml
---
name: researcher
tools: Read, Grep, Glob
model: sonnet
---
```

System prompt incluye obligatorio:
```
Output format:
1. Summary
2. Findings (con file:line)
3. Recommendations
4. Obstacles Encountered  ← surface workarounds para no redescubrir
```

### 9. Hybrid retrieval (RAG)

```python
# Vector (semantic) + BM25 (lexical) + RRF
rag = HybridSearch()
rag.index_documents(corpus)
results = rag.search(query, k=5)
```

### 10. Routing workflow

```python
category = classify(input)
if category == "programming":
    return run_programming_workflow(input)
elif category == "design":
    return run_design_workflow(input)
```

## Cost rules

- system prompt >1024 tokens → `cache_control` obligatorio
- Eval grading / dataset gen / batch → Haiku
- Main reasoning → Sonnet
- Orchestration con multi-step → Opus
- Streaming → solo UX percibida, no ahorro

## Ver también

- [DECISIONS.md](DECISIONS.md) — workflow vs agent decision matrix detallada
- [BEST_PRACTICES.md](BEST_PRACTICES.md) — síntesis cross-curso completa
- [COST_MODEL.md](COST_MODEL.md) — estimaciones
- [EXTERNAL_VALIDATOR.md](EXTERNAL_VALIDATOR.md) — Doble Filo protocol
