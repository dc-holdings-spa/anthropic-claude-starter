# External Validator Pattern (Doble Filo)

Dos chats Claude independientes brokereados por operador humano. Para high-stakes merges, security scaffolding, multi-branch sequences.

## Cuándo aplicar

- Merge a `main` con >500 LOC
- Cambios a auth / security / hooks
- Refactor multi-archivo cross-cutting
- Sprint final que cierra fase

NO aplicar para:
- Bugfixes triviales (<50 LOC)
- Docs only
- Tests only
- Iteración rápida en prototipo

## Protocolo

```
┌────────────────────────────────────────────────────────────┐
│  CHAT A — IMPLEMENTER                                      │
│  - Lee task spec                                           │
│  - Implementa backend + frontend + tests                   │
│  - Commits a feature branch (NO push)                      │
│  - Genera handoff packet                                   │
└────────────────┬───────────────────────────────────────────┘
                 │ Operador brokerea
                 ▼
┌────────────────────────────────────────────────────────────┐
│  CHAT B — VALIDATOR                                        │
│  - Lee handoff packet + DoD original                       │
│  - Audit independiente:                                    │
│    · contract drift                                        │
│    · regressions                                           │
│    · security                                              │
│    · perf                                                  │
│    · rollback safety                                       │
│  - Verdict: PASS | PASS_WITH_NITS | FAIL                   │
│  - Si PASS: merges + deploys                               │
│  - Si NITS: lista, operador decide                         │
│  - Si FAIL: correction packet → vuelta a Chat A            │
└────────────────────────────────────────────────────────────┘
```

## Handoff packet template (Chat A → operador → Chat B)

```
TASK: <description>
BRANCH: feat/<slug>
COMMITS: <list of SHAs>

DELIVERABLES:
  - Backend: <files + endpoints>
  - Frontend: <components + routes>
  - Migrations: <if any>
  - Tests: <paths + count>

DEMO STEPS: <numbered repro para validator>

KNOWN GAPS: <intencional deferred>

ROLLBACK: <git revert SHA, downgrade rev>
```

## Validator verdict template (Chat B → operador)

```
TASK: <ref>
VERDICT: PASS | PASS_WITH_NITS | FAIL

DoD CHECK:
  ✓ criterion 1
  ✓ criterion 2
  ✗ criterion 3 — razón

INDEPENDENT TESTS RUN:
  $ pytest tests/tier1   → 6/6 green
  $ curl /api/endpoint    → expected response

SECURITY:
  - auth: validated
  - injection: validated
  - leak surface: validated

PERF:
  - p50: 120ms
  - p99: 480ms

REGRESSIONS:
  - tested path X: still works
  - tested path Y: still works

FINDINGS:
  - [minor] file.py:42 typo in comment
  - [major] file.py:88 missing input validation
```

## Operador role

- Brokerea handoff (NO modifica el contenido)
- Lee packets
- Aplica verdict
- Si A y B disagree en finding → operador resuelve o escala a human review

NO mediates en substance. Cada chat es independiente intencional.

## Anti-patterns que prohíbe

- ❌ Mismo chat audita y implementa (sesgo)
- ❌ Validator tiene access al handoff packet ANTES de implementer terminar
- ❌ Implementer y validator se comunican directo
- ❌ Operador edita findings para reconciliar

## Origen

Single-chat tiende a:
- Auto-validar lo que implementó
- Saltarse DoD checks por confianza en su propia implementación
- Esconder gaps known

Dos chats independientes = imposible que se autoconvenzan. Brokerage operador = audit trail.

## Costos

- 2x token cost (dos chats)
- 1.5-2x calendar time
- Reduce defect rate ~70% en high-stakes merges (medido empíricamente)

Worth para changes con cost de regresión alto. Overkill para iteración rápida.
