"""
Eval pipeline framework. 5 pasos: dataset → run → grade → aggregate → iterate.

Referencia: CLAUDE-API-RESUMEN.md §Section 2 — Prompt evaluation.

Patrón: LLM-as-judge structured grade (score + strengths + weaknesses + reasoning).
Sin esto, el juez tiende al middle bias (6/10 por defecto).

Uso:
    from eval.pipeline import EvalPipeline

    pipeline = EvalPipeline(
        prompt_fn=my_prompt,
        criteria="Code should compile and pass tests",
    )
    dataset = pipeline.generate_dataset(n=20)
    report = pipeline.run(dataset)
    print(f"Avg score: {report['avg_score']:.2f}/5")
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from statistics import mean
from typing import Any

from anthropic import Anthropic

# Modelo barato para grading masivo (LLM-as-judge).
DEFAULT_JUDGE_MODEL = os.getenv("APP_BULK_MODEL", "claude-haiku-4-5")
DEFAULT_GENERATOR_MODEL = os.getenv("APP_BULK_MODEL", "claude-haiku-4-5")


class EvalPipeline:
    """Eval framework: dataset gen → run prompt → grade → aggregate."""

    def __init__(
        self,
        prompt_fn: Callable[[dict], str],
        criteria: str,
        judge_model: str = DEFAULT_JUDGE_MODEL,
        generator_model: str = DEFAULT_GENERATOR_MODEL,
    ) -> None:
        """
        prompt_fn: función que recibe test_case dict y retorna el prompt string a evaluar.
        criteria: descripción de qué evaluar (rubrica del juez).
        """
        self.prompt_fn = prompt_fn
        self.criteria = criteria
        self.judge_model = judge_model
        self.generator_model = generator_model
        self._client = Anthropic()

    # ------------------------------------------------------------------
    # Step 1: Dataset generation (LLM-as-generator).
    # ------------------------------------------------------------------
    def generate_dataset(self, n: int = 20, scenario_desc: str | None = None) -> list[dict]:
        """Haiku genera N test cases diversos en JSON puro (prefill + stop)."""
        desc = scenario_desc or self.criteria
        prompt = f"""Generate {n} diverse test cases for the following scenario:

{desc}

Output a JSON array. Each item must have:
- task: descripción del caso de prueba
- expected_format: formato esperado del output
- difficulty: "easy" | "medium" | "hard"

Cover edge cases, empty inputs, malformed inputs, happy path."""

        r = self._client.messages.create(
            model=self.generator_model,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "```json\n"},
            ],
            stop_sequences=["```"],
        )
        return json.loads(r.content[0].text)

    # ------------------------------------------------------------------
    # Step 2: Run prompt on each test case.
    # ------------------------------------------------------------------
    def _run_one(self, test_case: dict) -> str:
        prompt = self.prompt_fn(test_case)
        r = self._client.messages.create(
            model=self.generator_model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text.strip()

    # ------------------------------------------------------------------
    # Step 3: Grade via LLM-as-judge con structured output.
    # ------------------------------------------------------------------
    def _grade_one(self, test_case: dict, output: str) -> dict:
        eval_prompt = f"""You are an evaluator. Rate the output on a 1-5 scale.

Criteria: {self.criteria}

Test case: {json.dumps(test_case, ensure_ascii=False)}
Output: {output}

Respond with strict JSON only:
{{
  "score": <int 1-5>,
  "strengths": "<what was done well>",
  "weaknesses": "<what was lacking>",
  "reasoning": "<concrete justification>"
}}"""

        r = self._client.messages.create(
            model=self.judge_model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": eval_prompt},
                {"role": "assistant", "content": "```json\n"},
            ],
            stop_sequences=["```"],
        )
        try:
            return json.loads(r.content[0].text)
        except json.JSONDecodeError:
            # Fallback: extrae score por regex.
            m = re.search(r'"score"\s*:\s*(\d)', r.content[0].text)
            return {
                "score": int(m.group(1)) if m else 0,
                "strengths": "",
                "weaknesses": "parse failed",
                "reasoning": r.content[0].text[:200],
            }

    # ------------------------------------------------------------------
    # Step 4: Aggregate.
    # ------------------------------------------------------------------
    def run(self, dataset: list[dict]) -> dict[str, Any]:
        results = []
        for tc in dataset:
            output = self._run_one(tc)
            grade = self._grade_one(tc, output)
            results.append(
                {
                    "task": tc.get("task", ""),
                    "output": output,
                    **grade,
                }
            )

        scores = [r["score"] for r in results if isinstance(r.get("score"), int)]
        return {
            "n": len(results),
            "avg_score": mean(scores) if scores else 0.0,
            "distribution": {i: scores.count(i) for i in range(1, 6)},
            "results": results,
        }


__all__ = ["EvalPipeline"]
