Ejecuta eval pipeline sobre $ARGUMENTS (path al prompt file).

Pasos:
1. Cargar prompt desde $ARGUMENTS
2. Generar dataset de 20 test cases via `src/eval/pipeline.py:EvalPipeline.generate_dataset()`
3. Run prompt en cada test case
4. Grade via subagent `eval-grader` (LLM-as-judge structured)
5. Aggregate avg_score + distribution
6. Output: si avg_score >= 4.0 → PASS. Si <4.0 → FAIL con recomendaciones.

Si $ARGUMENTS vacío, lista todos los prompts en `src/prompts/` y pregunta cuál evaluar.