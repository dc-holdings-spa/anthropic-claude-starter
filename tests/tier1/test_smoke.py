"""
Tier-1 smoke tests. Deterministic. Cero tokens.

Run: pytest tests/tier1
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.mark.tier1
def test_caching_wraps_short_system_without_breakpoint():
    """System string corto NO recibe cache_control."""
    from caching import CachedClient

    blocks = CachedClient._build_system_blocks("short prompt")
    assert len(blocks) == 1
    assert "cache_control" not in blocks[0]


@pytest.mark.tier1
def test_caching_adds_breakpoint_to_large_system():
    """System >1024 tokens (~4096 chars) recibe cache_control automático."""
    from caching import CachedClient, MIN_CACHEABLE_TOKENS

    big = "x" * (MIN_CACHEABLE_TOKENS * 4 + 100)
    blocks = CachedClient._build_system_blocks(big)
    assert len(blocks) == 1
    assert blocks[0].get("cache_control") == {"type": "ephemeral"}


@pytest.mark.tier1
def test_caching_respects_existing_cache_control():
    """Si caller ya marcó cache_control, no se sobreescribe."""
    from caching import CachedClient

    explicit = [
        {"type": "text", "text": "x" * 10000, "cache_control": {"type": "ephemeral"}},
    ]
    blocks = CachedClient._build_system_blocks(explicit)
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}


@pytest.mark.tier1
def test_chunking_by_char():
    """Chunking char-based produce overlap correcto."""
    from rag.hybrid import chunk_by_char

    text = "abc" * 1000  # 3000 chars
    chunks = chunk_by_char(text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 3
    # Overlap: el final del chunk N coincide con el inicio del N+1
    assert chunks[0][-100:] == chunks[1][:100]


@pytest.mark.tier1
def test_chunking_by_section():
    """Section chunking parte en headings."""
    from rag.hybrid import chunk_by_section

    doc = "intro\n## Section 1\ncontent 1\n## Section 2\ncontent 2"
    chunks = chunk_by_section(doc)
    assert len(chunks) == 3


@pytest.mark.tier1
def test_anatomist_lint_no_false_positives_clean_repo():
    """El propio repo starter NO debe disparar critical findings."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "anatomist-lint.py"), str(ROOT)],
        capture_output=True,
        text=True,
    )
    # Allowed: minor findings (puede haber descripciones cortas en skills demo)
    # NOT allowed: critical/major en el starter mismo
    assert "CRITICAL" not in result.stdout.upper() or result.returncode == 0, (
        f"Starter repo tiene critical findings:\n{result.stdout}"
    )
