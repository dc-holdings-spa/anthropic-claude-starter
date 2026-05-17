"""Tier-1 tests para BudgetGuard. Deterministic. Cero tokens."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from budget import BudgetExceededError, BudgetGuard


def _mock_response(input_tokens=100, output_tokens=50, cached_read=0, cache_create=0):
    """Mock minimal del shape Anthropic Message.usage."""
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cached_read,
        cache_creation_input_tokens=cache_create,
    )
    return SimpleNamespace(usage=usage)


@pytest.mark.tier1
def test_budget_charge_accumulates():
    guard = BudgetGuard(max_usd=10.0)
    guard.charge(_mock_response(1000, 500), "claude-sonnet-4-5")
    # 1000 × $3/1M + 500 × $15/1M = $0.003 + $0.0075 = $0.0105
    assert 0.010 < guard.spent_usd < 0.011


@pytest.mark.tier1
def test_budget_raises_when_exceeded():
    guard = BudgetGuard(max_usd=0.001)  # límite muy bajo
    with pytest.raises(BudgetExceededError):
        guard.charge(_mock_response(10000, 10000), "claude-opus-4-7")


@pytest.mark.tier1
def test_budget_cached_read_discount():
    """Cached read tokens deben costar ~10% del regular input."""
    guard = BudgetGuard(max_usd=10.0)
    # 10000 cached_read en Sonnet: 10000 × $0.30/1M = $0.003
    guard.charge(_mock_response(0, 0, cached_read=10000), "claude-sonnet-4-5")
    assert 0.0029 < guard.spent_usd < 0.0031


@pytest.mark.tier1
def test_budget_unknown_model_fallback():
    """Modelo desconocido usa Sonnet pricing conservador."""
    guard = BudgetGuard(max_usd=10.0)
    guard.charge(_mock_response(1000, 500), "claude-unknown-model")
    assert guard.spent_usd > 0


@pytest.mark.tier1
def test_budget_remaining_and_pct():
    guard = BudgetGuard(max_usd=1.0)
    guard.charge(_mock_response(1000, 500), "claude-sonnet-4-5")
    assert guard.remaining_usd == pytest.approx(1.0 - guard.spent_usd)
    assert 0 < guard.pct_consumed < 100


@pytest.mark.tier1
def test_budget_report():
    guard = BudgetGuard(max_usd=10.0)
    guard.charge(_mock_response(1000, 500), "claude-sonnet-4-5", label="step-1")
    guard.charge(_mock_response(500, 200), "claude-haiku-4-5", label="grade-1")
    report = guard.report()
    assert "claude-sonnet-4-5" in report
    assert "claude-haiku-4-5" in report
    assert "Calls: 2" in report
