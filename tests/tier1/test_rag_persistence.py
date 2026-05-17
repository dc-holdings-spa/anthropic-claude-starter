"""Tier-1 tests para HybridSearch persistencia. Deterministic. Cero tokens."""

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from rag.hybrid import HybridSearch

# Skip si dep no instalada (CI con deps completas, dev env puede no tenerlas).
_bm25_available = pytest.importorskip("rank_bm25", reason="rank_bm25 no instalado")


@pytest.mark.tier1
def test_save_load_index_roundtrip():
    """Save + load deben preservar chunks + BM25 (vector lo skipea si no hay key)."""
    rag = HybridSearch()
    docs = [
        "Authentication module JWT-based",
        "Database Postgres 16 with replicas",
        "Frontend Next.js App Router",
    ]
    rag.index_documents(docs)

    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        rag.save_index(path)

        # Cargar en instancia nueva
        rag2 = HybridSearch()
        rag2.load_index(path)

        assert len(rag2.chunks) == 3
        assert rag2.chunks[0].text == "Authentication module JWT-based"
        # BM25 reconstruido
        assert rag2.bm25 is not None
    finally:
        Path(path).unlink(missing_ok=True)


@pytest.mark.tier1
def test_bm25_search_after_load_works():
    """BM25 lexical search debe seguir funcionando post-load."""
    rag = HybridSearch()
    rag.index_documents(
        [
            "Section about JWT tokens and authentication",
            "Section about Postgres database tuning",
            "Section about React frontend components",
        ]
    )

    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        rag.save_index(path)

        rag2 = HybridSearch()
        rag2.load_index(path)

        results = rag2.search("JWT", k=2)
        # Top result debe ser el chunk sobre JWT
        assert len(results) > 0
        top_chunk = results[0][1]
        assert "JWT" in top_chunk.text
    finally:
        Path(path).unlink(missing_ok=True)
