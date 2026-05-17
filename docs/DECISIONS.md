# Decisions — Workflow vs Agent

Decisión más importante al diseñar una app Claude. Default: workflow. Fallback: agent.

## Regla maestra

> Si conocés la **secuencia exacta de pasos** → workflow.
> Si NO sabés exactly qué pasos → agent.

## Decision matrix

| Pregunta | Workflow | Agent |
|----------|----------|-------|
| ¿Sé qué tools usaré? | sí, lista finita | no, depende del input |
| ¿Sé el orden? | sí, fijo | no, Claude decide |
| ¿Necesito predictibilidad? | sí | no es prioridad |
| ¿Testeable? | sí, easy | no, hard |
| ¿Success rate aceptable? | >90% | ~70-80% |
| ¿Flexibilidad runtime? | rígido | dinámico |
| ¿Costo predecible? | sí | variable |
| ¿Quiero medir cada paso? | sí | n/a |

Si la mayoría son "sí" en columna workflow → workflow.

## Patrones workflow específicos

### Chaining

```
[input] → step1 → step2 → step3 → [output]
```

Cuándo: tareas con dependencia output→input clara. Ej: extract → summarize → format.

### Routing

```
[input] → classify → ├── workflow_A
                      ├── workflow_B
                      └── workflow_C
```

Cuándo: tipos distintos de input necesitan distinto handling. Ej: support tickets clasificados → agente especialista por tipo.

### Parallelization

```
[input] → split → ├── task_A ──┐
                  ├── task_B ──┤ → consolidate → [output]
                  └── task_C ──┘
```

Cuándo: sub-tareas independientes que pueden correr paralelo. Ej: análisis múltiples criterios + reporte consolidado.

### Orchestrator-workers

```
[input] → orchestrator → ├── worker_1 (decide)
                          ├── worker_2 (decide)
                          └── synthesize result
```

Cuándo: orchestrator delega + sintetiza.

### Evaluator-optimizer

```
generate → evaluate → if pass: return
                       if fail: regenerate (loop)
```

Cuándo: calidad varía y querés iterar. Ej: refinar prompt hasta score >4.0.

## Cuándo usar agent (no workflow)

Casos legítimos:

1. **Open-ended exploration** — "investigá X codebase, encontrá Y"
2. **Multi-tool combinatoria desconocida** — "agendá reunión" puede ser get_time + add_duration + create_event + send_invite en cualquier combo
3. **Tasks con variabilidad alta** — debugger que no sabés qué error tendrás
4. **Computer use** — UI cambia dinámicamente

NO usar agent para:

1. ❌ "Genera resumen de documento" (workflow chaining)
2. ❌ "Clasifica email + responde" (workflow routing)
3. ❌ "Revisa código" (subagent estructurado, no agent open-ended)

## Tools para agents

Si vas con agent, principios:

1. **Abstract tools > Specific tools** — `read_file` + `run_command` mejor que `parse_python_function` + `extract_imports`. Más combinables.
2. **Least privilege** — solo tools que realmente necesita
3. **Environment inspection obligatorio** — post tool call, re-leer state (screenshot/list/query)
4. **Stopping criterion explícito** — output format estructurado fuerza terminación

## Anti-patterns evitar

- ❌ Agent porque "es más cool" — workflow simpler is better
- ❌ Sequential pipeline donde step N depende de step N-1 (info loss en handoff de subagent)
- ❌ Test runner agent que esconde output (performó peor que todos los configs en testing del curso)
- ❌ "Expert" persona claim (`you are a Python expert`) — Claude ya tiene knowledge

## Producción rule

> Default a workflow simple. Pivot a agent solo cuando hay evidencia que el workflow falla.

Mide tu workflow con eval pipeline antes de "upgrade" a agent.
