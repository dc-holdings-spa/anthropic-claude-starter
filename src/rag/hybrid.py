"""
Hybrid RAG: chunking + vector search (Voyage AI) + BM25 lexical + Reciprocal Rank Fusion.

Referencia: CLAUDE-API-RESUMEN.md §Section 5 — RAG and Agentic Search.

Por qué hybrid: vector search falla con exact-match codes/IDs (ej "INC-2023-Q4-011").
BM25 los rescata. RRF combina rankings sin tuning manual.

Uso:
    from rag.hybrid import HybridSearch

    rag = HybridSearch()
    rag.index_documents(["doc text 1", "doc text 2", ...])
    results = rag.search("Q4 incident", k=5)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

try:
    import voyageai
except ImportError:
    voyageai = None  # type: ignore

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None  # type: ignore

import numpy as np


@dataclass
class Chunk:
    """Unidad mínima de retrieval."""

    text: str
    source: str = ""
    metadata: dict | None = None


# ----------------------------------------------------------------------
# Chunking strategies.
# ----------------------------------------------------------------------
def chunk_by_char(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """Char-based chunking. Simple. Ignora estructura."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def chunk_by_sentence(
    text: str, max_per_chunk: int = 5, overlap: int = 1
) -> list[str]:
    """Sentence-based. Mejor que char, preserva oraciones completas."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    i = 0
    while i < len(sentences):
        chunk = " ".join(sentences[i : i + max_per_chunk])
        chunks.append(chunk)
        i += max_per_chunk - overlap
    return chunks


def chunk_by_section(doc: str, pattern: str = r"\n##\s+") -> list[str]:
    """Section-based. Preserva estructura semántica del documento."""
    return [c.strip() for c in re.split(pattern, doc) if c.strip()]


# ----------------------------------------------------------------------
# Hybrid search engine.
# ----------------------------------------------------------------------
class HybridSearch:
    """Vector search (Voyage) + BM25 lexical + Reciprocal Rank Fusion.

    Soporta persistencia de embeddings via save_index/load_index — evita
    re-embedding masivo en cada run (costo Voyage real).
    """

    def __init__(
        self,
        voyage_model: str = "voyage-3",
        rrf_k: int = 60,
    ) -> None:
        self.voyage_model = voyage_model
        self.rrf_k = rrf_k
        self.chunks: list[Chunk] = []
        self.embeddings: np.ndarray | None = None
        self.bm25: BM25Okapi | None = None
        self._voyage = None

        if voyageai is not None and os.getenv("VOYAGE_API_KEY"):
            self._voyage = voyageai.Client()

    # ------------------------------------------------------------------
    # Persistence.
    # ------------------------------------------------------------------
    def save_index(self, path: str | os.PathLike) -> None:
        """Persiste chunks + embeddings + bm25 index a disco.

        Formato: numpy `.npz` archive con:
        - chunks_text, chunks_source, chunks_metadata (object arrays)
        - embeddings (float32 matrix)
        - bm25_corpus (tokenized lists)
        - meta: voyage_model, rrf_k
        """
        import json
        import pathlib

        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        bm25_corpus = [c.text.lower().split() for c in self.chunks] if self.bm25 else []

        np.savez(
            path,
            chunks_text=np.array([c.text for c in self.chunks], dtype=object),
            chunks_source=np.array([c.source for c in self.chunks], dtype=object),
            chunks_metadata=np.array(
                [json.dumps(c.metadata or {}) for c in self.chunks], dtype=object
            ),
            embeddings=self.embeddings if self.embeddings is not None else np.array([]),
            bm25_corpus=np.array(bm25_corpus, dtype=object),
            meta=np.array(
                [json.dumps({"voyage_model": self.voyage_model, "rrf_k": self.rrf_k})],
                dtype=object,
            ),
        )

    def load_index(self, path: str | os.PathLike) -> None:
        """Carga index previamente guardado. Reemplaza state actual."""
        import json

        data = np.load(path, allow_pickle=True)

        texts = data["chunks_text"]
        sources = data["chunks_source"]
        metas = data["chunks_metadata"]
        self.chunks = [
            Chunk(text=str(t), source=str(s), metadata=json.loads(str(m)))
            for t, s, m in zip(texts, sources, metas, strict=True)
        ]

        emb = data["embeddings"]
        self.embeddings = emb if emb.size > 0 else None

        bm25_corpus = data["bm25_corpus"]
        if BM25Okapi is not None and len(bm25_corpus) > 0:
            self.bm25 = BM25Okapi(list(bm25_corpus))

    def index_documents(self, docs: list[str | Chunk]) -> None:
        """Indexa documentos. Construye embeddings + BM25."""
        self.chunks = [
            doc if isinstance(doc, Chunk) else Chunk(text=doc) for doc in docs
        ]

        if self._voyage is not None:
            texts = [c.text for c in self.chunks]
            result = self._voyage.embed(
                texts, model=self.voyage_model, input_type="document"
            )
            self.embeddings = np.array(result.embeddings)

        if BM25Okapi is not None:
            tokenized = [c.text.lower().split() for c in self.chunks]
            self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, k: int = 5) -> list[tuple[float, Chunk]]:
        """Búsqueda hybrid con RRF. Retorna top-k (rrf_score, chunk)."""
        if not self.chunks:
            return []

        vector_ranks = self._vector_search(query) if self._voyage else {}
        bm25_ranks = self._bm25_search(query) if self.bm25 else {}

        # Reciprocal Rank Fusion: score = sum(1 / (k + rank)).
        rrf_scores: dict[int, float] = {}
        for idx, rank in vector_ranks.items():
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (self.rrf_k + rank)
        for idx, rank in bm25_ranks.items():
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (self.rrf_k + rank)

        top = sorted(rrf_scores.items(), key=lambda x: -x[1])[:k]
        return [(score, self.chunks[idx]) for idx, score in top]

    def _vector_search(self, query: str) -> dict[int, int]:
        """Devuelve {chunk_idx: rank} desde 1."""
        q_emb = np.array(
            self._voyage.embed(
                [query], model=self.voyage_model, input_type="query"
            ).embeddings[0]
        )
        # Cosine similarity.
        norms = np.linalg.norm(self.embeddings, axis=1)  # type: ignore[arg-type]
        q_norm = np.linalg.norm(q_emb)
        sims = (self.embeddings @ q_emb) / (norms * q_norm + 1e-9)  # type: ignore[operator]
        order = np.argsort(-sims)
        return {int(idx): rank + 1 for rank, idx in enumerate(order)}

    def _bm25_search(self, query: str) -> dict[int, int]:
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)  # type: ignore[union-attr]
        order = sorted(range(len(scores)), key=lambda i: -scores[i])
        return {idx: rank + 1 for rank, idx in enumerate(order)}


__all__ = [
    "Chunk",
    "HybridSearch",
    "chunk_by_char",
    "chunk_by_sentence",
    "chunk_by_section",
]
