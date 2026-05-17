# Examples — end-to-end demos

## demo_chatbot.py

Combina **caching + RAG hybrid + eval pipeline** en un solo flow. Caso uso: chatbot que responde sobre `sample_corpus.md`.

### Run

```bash
# Single question
python examples/demo_chatbot.py "What incident happened with JWT?"

# Eval pipeline completo
python examples/demo_chatbot.py --eval
```

### Qué demuestra

| Componente | Pattern aplicado |
|------------|------------------|
| `CachedClient` | Auto `cache_control` en context blocks grandes (90% off en repeats) |
| `HybridSearch` | Voyage embeddings + BM25 lexical + RRF |
| `chunk_by_section` | Chunking semántico por headings |
| Eval grading | LLM-as-judge structured (score + reasoning) |

### Costo estimado

- 1 query: ~$0.005 (Sonnet, ~1k tokens context cached)
- Eval pipeline (5 questions): ~$0.025

### Esperado output

```
=== Indexing corpus ===
  Indexed 7 chunks
  Vector available: True   (si VOYAGE_API_KEY set)
  BM25 available: True

  [usage] in=850 out=120 cache_read=0 cache_create=850
The JWT signature mismatch incident INC-2026-001 occurred on 2026-03-15,
causing a 30-minute outage. Root cause: secret rotation deployed without
grace period.
```

Segundo run con misma pregunta → `cache_read=850, cache_create=0` → costo reducido 90%.
