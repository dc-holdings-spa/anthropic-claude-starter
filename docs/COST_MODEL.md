# Cost Model

Estimaciones realistas por tipo de operación. Pricing Anthropic 2026 (verificar `console.anthropic.com/billing`).

## Pricing por modelo (USD per million tokens)

| Modelo | Input | Output | Cached input | Notas |
|--------|-------|--------|--------------|-------|
| Opus 4.7 | $15 | $75 | $1.50 | Orchestration |
| Sonnet 4.5 | $3 | $15 | $0.30 | Main reasoning (default) |
| Haiku 4.5 | $0.80 | $4 | $0.08 | Bulk / grading / dataset gen |

Cached read = 90% off input cost. Cache creation = 25% premium en primer call.

## Ejemplos típicos

### Single API request

```
~500 input + 200 output tokens (Sonnet)
= 500 × $3/1M + 200 × $15/1M
= $0.0015 + $0.003
= ~$0.005 por request
```

### Multi-turn conversación (10 turns)

```
Historial crece linealmente. Turn N envía N×promedio tokens.
10 turns avg 500 in/200 out, sin caching:
= sum(N × 500) × $3/1M + 10 × 200 × $15/1M
= 27500 × $3/1M + 2000 × $15/1M
= $0.083 + $0.030
= ~$0.11 por conversación
```

Con caching en system prompt (3KB persona):
- Sin cache: 10 × 750 tokens × $3/1M = $0.0225 solo en re-enviar persona
- Con cache: $0.0225 × 0.10 = $0.00225 → ahorro 90%

### Eval pipeline (20 test cases)

```
Dataset gen (Haiku): 1 call, ~1k in / 2k out
= 1000 × $0.80/1M + 2000 × $4/1M = $0.001 + $0.008 = $0.009

Run prompt (Haiku, 20 cases): 20 calls, avg 300 in / 200 out
= 20 × (300 × $0.80/1M + 200 × $4/1M)
= 20 × ($0.00024 + $0.0008) = $0.021

Grade by judge (Haiku, 20 cases): 20 calls, avg 500 in / 300 out
= 20 × (500 × $0.80/1M + 300 × $4/1M)
= 20 × ($0.0004 + $0.0012) = $0.032

Total eval pipeline: ~$0.06
```

### Subagent invocation

```
Subagent (Sonnet): system prompt 2KB + 3 tool calls + 1KB output
~3000 in + 1000 out
= 3000 × $3/1M + 1000 × $15/1M = $0.009 + $0.015 = $0.024
```

### Multi-agent orchestration run

```
1 run con orchestrator + 5 specialists + reporter:
- Orchestrator (Opus): ~50 turns, avg 3k in / 1k out = ~$3
- Specialists (Sonnet): 5 × 10 turns, avg 2k in / 800 out = ~$1.5
- Reporter (Opus): final pass, 5k in / 3k out = ~$0.30
Total: ~$5 por run

Target ceiling: ≤$15/run.
```

## Optimizaciones probadas

| Optimización | Ahorro | Esfuerzo |
|--------------|--------|----------|
| Prompt caching en system prompts >1024 tok | 70-90% en tokens cacheados | 2h |
| Switch a Haiku para grading/dataset | 75% vs Sonnet | 1h |
| Subagent para research (vs main thread) | 30-50% en context size | 4h |
| Structured output (cap output tokens) | 20-40% en output cost | 2h |
| Skip "expert" framing (cero value) | 5-10% en prompt size | 1h |

## Budget guard pattern

```python
class BudgetGuard:
    def __init__(self, max_usd: float = 15.0):
        self.max_usd = max_usd
        self.spent = 0.0

    def estimate_cost(self, usage, model: str) -> float:
        # Lookup pricing por modelo
        ...

    def check_and_charge(self, response, model: str) -> bool:
        cost = self.estimate_cost(response.usage, model)
        if self.spent + cost > self.max_usd:
            raise BudgetExceededError(...)
        self.spent += cost
        return True
```

Aplicar antes de cada call. Falla fast si exceedance.

## Métricas a trackear

- `tokens_input` / `tokens_output` / `tokens_cached_read` / `tokens_cached_creation`
- `cost_usd_per_call`
- `cost_usd_per_engagement`
- `cache_hit_rate` (cached_read / total_input)

Si `cache_hit_rate < 30%` en system prompts grandes → review breakpoint placement.
