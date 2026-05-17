---
name: code-audit
description: Audita codebase contra anti-patterns Anthropic best-practices. Usar cuando user pide audit, audit anti-patterns, revisar contra best-practices, o `/audit`.
---

# Code audit — Anti-pattern detection

Audita el codebase actual contra los 10 anti-patterns destilados de cursos Anthropic.

## Procedimiento

Para cada anti-pattern, ejecuta el check correspondiente y reporta findings.

## Anti-patterns checklist

### 1. API key en frontend / código

```bash
grep -rE "(sk-ant-|ANTHROPIC_API_KEY\s*=\s*['\"])" --include="*.{js,ts,tsx,html,vue}" .
```

→ Si hay matches en archivos frontend → CRITICAL.

### 2. Substring/regex classifiers para contenido semántico

```bash
grep -rE "(_CREDENTIAL|_HINTS|_DEFAULTS|_PATTERNS).*=\s*(frozenset|set|\[)" --include="*.py" .
```

→ Si hay diccionarios de hints con substrings → MAJOR (rule 4 violation).

### 3. Hooks con path relativo

```bash
grep -rE '"command":\s*"[^/$]' .claude/settings*.json 2>/dev/null
```

→ Path no absoluto = T1574.007 risk → CRITICAL.

### 4. Tool descriptions vagas / similares

```bash
grep -A2 -B1 "description:" .claude/agents/*.md .claude/skills/*/SKILL.md | head -50
```

→ Manual review: descriptions <20 chars o muy similares entre roles → MAJOR.

### 5. Expert claim subagents

```bash
grep -rE "you are (a |an )?(an? )?(expert|specialist|guru|wizard)" .claude/agents/ .claude/skills/ 2>/dev/null
```

→ MINOR — cero value add, Claude ya tiene knowledge.

### 6. Sequential pipelines con dependencia

Manual: revisar si hay subagents encadenados donde paso N depende de paso N-1.
→ MAJOR — info loss en handoff.

### 7. Test runner subagents

```bash
grep -lE "test.*runner|run.*tests" .claude/agents/*.md 2>/dev/null
```

→ Si el agent devuelve solo pass/fail sin output → MAJOR.

### 8. Tool allowlist > 15 sin justificación

```bash
for f in .claude/agents/*.md; do
    count=$(grep -oE 'tools:\s*[^[:space:]]+' "$f" | tr ',' '\n' | wc -l)
    [ "$count" -gt 15 ] && echo "$f: $count tools"
done
```

→ Least-privilege violation si >15 sin doc.

### 9. Tested-once código

```bash
find src -name "*.py" -newer pyproject.toml | xargs -I{} sh -c 'grep -L "test_" tests/ 2>/dev/null || echo "{}"'
```

→ Manual: código nuevo sin test correspondiente → MAJOR.

### 10. Prompt caching no aprovechado

```bash
grep -rE "messages\.create\(" --include="*.py" src/ | grep -v cache_control
```

→ Si hay system prompts >1024 tokens sin cache_control → MINOR (cost waste).

## Output formato

```
# Audit Report — <fecha>

## CRITICAL
(0+ items)

## MAJOR
(0+ items)

## MINOR
(0+ items)

## Summary
N findings total. M critical. Top recommendation: <action>.
```
