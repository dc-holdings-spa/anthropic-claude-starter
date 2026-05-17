"""
Claude client wrapper con prompt caching automático.

Aplica cache_control={"type":"ephemeral"} a system blocks que excedan 1024 tokens
(threshold mínimo de Anthropic). Reduce costo hasta 90% en tokens cacheados.

Referencia: CLAUDE-API-RESUMEN.md §Section 6 — Prompt caching.

Uso:
    from caching import CachedClient

    client = CachedClient(model="claude-sonnet-4-5")
    response = client.create(
        system="You are a helpful assistant" + LARGE_CONTEXT,
        messages=[{"role": "user", "content": "..."}],
        max_tokens=1000,
    )
    # Subsequent calls con same system → 90% off cached input tokens.
"""

from __future__ import annotations

import os
from typing import Any

# Mínimo Anthropic para que un bloque sea cacheable.
MIN_CACHEABLE_TOKENS = 1024
# Heurística: ~4 chars por token. Conservador.
MIN_CACHEABLE_CHARS = MIN_CACHEABLE_TOKENS * 4


class CachedClient:
    """Wrapper Anthropic client que aplica cache_control automático.

    Lazy-imports `anthropic` package — permite que `_build_system_blocks`
    sea testeable sin SDK instalado.

    Soporta sync (`create`) y async (`acreate`).
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        from anthropic import Anthropic, AsyncAnthropic  # lazy import

        self.model = model or os.getenv("APP_DEFAULT_MODEL", "claude-sonnet-4-5")
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = Anthropic(api_key=api_key)
        self._async_client = AsyncAnthropic(api_key=api_key)

    def create(
        self,
        messages: list[dict],
        system: str | list | None = None,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Any:
        """Wrapper sync. cache_control auto en system blocks >1024 tok."""
        system_blocks = self._build_system_blocks(system) if system else None

        return self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            **kwargs,
        )

    async def acreate(
        self,
        messages: list[dict],
        system: str | list | None = None,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Any:
        """Wrapper async. Mismo behavior que create() con AsyncAnthropic."""
        system_blocks = self._build_system_blocks(system) if system else None

        return await self._async_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            **kwargs,
        )

    @staticmethod
    def _build_system_blocks(system: str | list) -> list[dict]:
        """Convierte string/lista system en bloques con cache_control auto."""
        if isinstance(system, str):
            # String simple: si supera mínimo cacheable, agrega breakpoint.
            block: dict = {"type": "text", "text": system}
            if len(system) >= MIN_CACHEABLE_CHARS:
                block["cache_control"] = {"type": "ephemeral"}
            return [block]

        # Lista: aplica cache_control al último bloque que califica.
        result: list[dict] = []
        for item in system:
            if isinstance(item, str):
                block = {"type": "text", "text": item}
            else:
                block = dict(item)
            # Marca cacheable si supera mínimo.
            text = block.get("text", "")
            if (
                len(text) >= MIN_CACHEABLE_CHARS
                and "cache_control" not in block
            ):
                block["cache_control"] = {"type": "ephemeral"}
            result.append(block)
        return result

    def cache_stats(self, response: Any) -> dict[str, int]:
        """Extrae métricas de caching de la respuesta."""
        usage = response.usage
        return {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_input_tokens": getattr(
                usage, "cache_creation_input_tokens", 0
            ) or 0,
            "cache_read_input_tokens": getattr(
                usage, "cache_read_input_tokens", 0
            ) or 0,
        }


__all__ = ["CachedClient", "MIN_CACHEABLE_TOKENS"]
