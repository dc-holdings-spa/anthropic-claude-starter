"""
Budget guard. Trackea costo acumulado de API calls. Falla fast cuando excede límite.

Referencia: COST_MODEL.md — Budget guard pattern.

Uso:
    from budget import BudgetGuard

    guard = BudgetGuard(max_usd=15.0)
    response = client.create(...)
    guard.charge(response, model="claude-sonnet-4-5")
    # raises BudgetExceededError si supera límite.

Pricing 2026 — actualizar al lanzamiento de nuevos modelos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class BudgetExceededError(Exception):
    """Lanzada cuando una charge supera max_usd."""


# Pricing USD per million tokens — 2026.
# Cached input = 90% off del input cost.
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 15.0, "output": 75.0, "cached_read": 1.5, "cache_create": 18.75},
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0, "cached_read": 0.3, "cache_create": 3.75},
    "claude-haiku-4-5": {"input": 0.8, "output": 4.0, "cached_read": 0.08, "cache_create": 1.0},
}


@dataclass
class BudgetGuard:
    """Acumula costo. Lanza si supera max_usd."""

    max_usd: float = 15.0
    spent_usd: float = 0.0
    calls: list[dict] = field(default_factory=list)

    def estimate_cost(self, usage: Any, model: str) -> float:
        """Calcula costo de un usage object (Anthropic SDK)."""
        prices = PRICING.get(model)
        if prices is None:
            # Modelo desconocido — usa Sonnet pricing como fallback conservador.
            prices = PRICING["claude-sonnet-4-5"]

        cached_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
        # Input tokens NO incluye cached_read en Anthropic API (es campo separado).
        regular_input = usage.input_tokens
        output = usage.output_tokens

        cost = (
            regular_input * prices["input"] / 1_000_000
            + output * prices["output"] / 1_000_000
            + cached_read * prices["cached_read"] / 1_000_000
            + cache_create * prices["cache_create"] / 1_000_000
        )
        return cost

    def charge(self, response: Any, model: str, label: str = "") -> float:
        """Suma costo del response al accumulator. Raises si excede max."""
        cost = self.estimate_cost(response.usage, model)
        next_total = self.spent_usd + cost
        self.calls.append(
            {
                "label": label,
                "model": model,
                "cost_usd": cost,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )
        if next_total > self.max_usd:
            raise BudgetExceededError(
                f"Budget exceeded: spent ${self.spent_usd:.4f} + ${cost:.4f} "
                f"= ${next_total:.4f} > ${self.max_usd:.2f} limit"
            )
        self.spent_usd = next_total
        return cost

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.max_usd - self.spent_usd)

    @property
    def pct_consumed(self) -> float:
        return (self.spent_usd / self.max_usd * 100) if self.max_usd > 0 else 0.0

    def report(self) -> str:
        """Texto resumen del gasto."""
        by_model: dict[str, float] = {}
        for c in self.calls:
            by_model[c["model"]] = by_model.get(c["model"], 0) + c["cost_usd"]
        lines = [
            f"Budget report — ${self.spent_usd:.4f} / ${self.max_usd:.2f} ({self.pct_consumed:.1f}%)",
            f"Calls: {len(self.calls)}",
        ]
        for m, c in sorted(by_model.items(), key=lambda x: -x[1]):
            lines.append(f"  {m}: ${c:.4f}")
        return "\n".join(lines)


__all__ = ["BudgetGuard", "BudgetExceededError", "PRICING"]
