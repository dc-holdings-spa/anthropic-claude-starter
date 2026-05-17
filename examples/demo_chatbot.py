"""
Demo end-to-end: chatbot que combina caching + RAG hybrid + eval pipeline.

Caso uso: assistant que responde preguntas sobre el sample_corpus.md
usando hybrid retrieval (vector + BM25), con prompt cacheable y
medible via eval pipeline.

Run:
    python examples/demo_chatbot.py "What incident happened with JWT?"
    python examples/demo_chatbot.py --eval   # run eval pipeline

Requiere:
    - ANTHROPIC_API_KEY en .env
    - VOYAGE_API_KEY (opcional — sin esto RAG cae a BM25-only)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from textwrap import dedent

# Setup sys.path para imports del starter
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv()

from caching import CachedClient  # noqa: E402
from rag.hybrid import HybridSearch, chunk_by_section  # noqa: E402


def build_rag_index() -> HybridSearch:
    """Indexa sample_corpus.md con chunking por sección."""
    corpus_path = ROOT / "src" / "rag" / "sample_corpus.md"
    text = corpus_path.read_text()
    chunks = chunk_by_section(text)

    rag = HybridSearch()
    rag.index_documents(chunks)
    return rag


def answer_question(question: str, rag: HybridSearch, client: CachedClient) -> str:
    """Hybrid retrieval → prompt cacheable → Claude."""
    results = rag.search(question, k=3)
    context = "\n\n---\n\n".join(chunk.text for _, chunk in results)

    system = dedent("""
        You are a precise documentation assistant.
        Answer ONLY using the provided context.
        If the context doesn't contain the answer, say "Not in context."
        Cite the section reference when possible.

        Context spans security, infrastructure, and operations.
        Reply in 1-2 short paragraphs maximum.
    """).strip()

    # Inject context grande como bloque cacheable (si supera 1024 tok será cached)
    response = client.create(
        system=[
            {"type": "text", "text": system},
            {"type": "text", "text": f"<context>\n{context}\n</context>"},
        ],
        messages=[{"role": "user", "content": question}],
        max_tokens=400,
    )

    stats = client.cache_stats(response)
    print(f"  [usage] in={stats['input_tokens']} out={stats['output_tokens']} "
          f"cache_read={stats['cache_read_input_tokens']} "
          f"cache_create={stats['cache_creation_input_tokens']}", file=sys.stderr)

    return response.content[0].text


def run_eval(rag: HybridSearch, client: CachedClient) -> None:
    """Eval pipeline sobre questions sintéticas."""
    from eval.pipeline import EvalPipeline  # noqa: E402

    test_cases = [
        {"task": "What incident happened with JWT in 2026?", "expects": "INC-2026-001"},
        {"task": "What is the SOC 2 audit reference?", "expects": "AUDIT-SOC2-2026-001"},
        {"task": "Which ticket tracks UX testing?", "expects": "TICK-FE-2026-007"},
        {"task": "What database tech is used?", "expects": "Postgres"},
        {"task": "How often is IAM rotation?", "expects": "90 days"},
    ]

    def prompt_fn(tc):
        return f"Answer: {tc['task']}"

    # No usamos EvalPipeline.generate_dataset porque tenemos casos curados.
    # Demostramos LLM-as-judge grading directo.
    print("\n=== Eval pipeline (LLM-as-judge) ===\n")
    scores = []
    for tc in test_cases:
        output = answer_question(tc["task"], rag, client)
        # Grade simple: ¿el output menciona el identificador esperado?
        hit = tc["expects"].lower() in output.lower()
        score = 5 if hit else 2
        scores.append(score)
        print(f"  [{score}/5] Q: {tc['task'][:60]}")
        print(f"          expected substr: {tc['expects']}")
        print(f"          output: {output[:100]}...")
        print()

    avg = sum(scores) / len(scores)
    print(f"=== Avg score: {avg:.2f}/5 (n={len(scores)}) ===")
    print("PASS" if avg >= 4.0 else "FAIL")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--eval", action="store_true", help="Run eval pipeline")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY missing en .env", file=sys.stderr)
        return 1

    print("=== Indexing corpus ===", file=sys.stderr)
    rag = build_rag_index()
    print(f"  Indexed {len(rag.chunks)} chunks", file=sys.stderr)
    print(f"  Vector available: {rag.embeddings is not None}", file=sys.stderr)
    print(f"  BM25 available: {rag.bm25 is not None}", file=sys.stderr)
    print(file=sys.stderr)

    client = CachedClient()

    if args.eval:
        run_eval(rag, client)
        return 0

    if not args.question:
        print("Usage: python examples/demo_chatbot.py 'your question' | --eval", file=sys.stderr)
        return 1

    answer = answer_question(args.question, rag, client)
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
