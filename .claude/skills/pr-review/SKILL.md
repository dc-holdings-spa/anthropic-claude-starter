---
name: pr-review
description: Reviewea PR diff con checklist security + quality + cost + best-practices. Usar cuando user pide PR review, code review, revisar diff, o `/review`.
---

# PR Review checklist

Output estructurado con secciones obligatorias.

## Pre-flight

1. `git diff main...HEAD` para ver cambios reales
2. Si hay >500 LOC de diff, identifica componentes principales antes de revisar

## Review en formato estructurado

```
## Summary
1 oración: qué hace este PR

## Critical Issues
(bloquean merge — bugs, security vulns, data integrity)

- [path/to/file.py:42] descripción del issue

## Major Issues
(quality / arch / perf significant)

## Minor Issues
(style / docs / micro-opts)

## Recommendations
(refactors sugeridos)

## Approval Status
- [ ] LGTM
- [ ] LGTM con nits
- [ ] Request changes

## Obstacles Encountered
(dependencias raras, env quirks, workarounds visibles en el diff)
```

## Reglas anti-pattern (block merge si aplican)

- ❌ API key hardcoded en código
- ❌ `.env` referenced sin gitignore check
- ❌ Substring/regex classifiers para contenido semántico
- ❌ Hooks con path relativo (T1574.007)
- ❌ Tool descriptions vagas o similares entre tools
- ❌ Subagents sin allowed-tools restrictivo
- ❌ Tests skipped sin justificación

## Cost-awareness

- ¿Llamadas Claude sin cache_control en system prompts grandes?
- ¿Modelo Opus usado donde Haiku basta?
- ¿Loops sin budget guard?

Surface estos en Recommendations sección.
