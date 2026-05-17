"""
MCP server demo con FastMCP. Tool + Resource (direct + templated) + Prompt.

Referencia: INTRO-MCP-RESUMEN.md.

Run:
    pip install mcp
    mcp dev src/mcp_servers/demo.py
    # Abre Inspector en http://localhost:6277

Concepts:
- Tool: model decide cuándo invocar
- Resource direct: URI estática, user fetcha
- Resource templated: URI con {param}, SDK parsea
- Prompt: template pre-testeada, user invoca
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

# In-memory storage. Producción: DB.
_docs = {
    "readme.md": "# Demo project\n\nStarter Anthropic app",
    "policy.md": "Security policy: rotate keys every 90 days",
}


# ----------------------------------------------------------------------
# Tools (model-decided actions).
# ----------------------------------------------------------------------
@mcp.tool()
def add_integers(a: int, b: int) -> int:
    """Suma dos enteros y retorna el resultado.

    Args:
        a: Primer entero
        b: Segundo entero
    """
    return a + b


@mcp.tool()
def list_documents() -> list[str]:
    """Lista todos los IDs de documentos disponibles."""
    return list(_docs.keys())


# ----------------------------------------------------------------------
# Resources (user-fetched data).
# ----------------------------------------------------------------------
@mcp.resource("docs://documents", mime_type="application/json")
def docs_list() -> list[str]:
    """Resource directo: URI estática. Lista todos los doc IDs."""
    return list(_docs.keys())


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def docs_fetch(doc_id: str) -> str:
    """Resource templated: URI con {doc_id} parameter. SDK parsea el ID."""
    if doc_id not in _docs:
        raise ValueError(f"Document {doc_id} not found")
    return _docs[doc_id]


# ----------------------------------------------------------------------
# Prompts (user-invoked templates, pre-tested).
# ----------------------------------------------------------------------
@mcp.prompt()
def summarize_document(doc_id: str) -> str:
    """Plantilla pre-testeada para resumir un documento."""
    content = _docs.get(doc_id, "")
    return f"""Resume el siguiente documento en exactamente 1 oración:

<document>
{content}
</document>

Reglas:
- Solo 1 oración
- Sin meta-comentarios sobre el formato
"""


@mcp.prompt()
def code_review_checklist() -> str:
    """Plantilla pre-testeada para review de código."""
    return """Realiza review estructurado del código provisto:

1. **Summary** — qué hace este código
2. **Critical Issues** — bugs, security vulns, data risks
3. **Major Issues** — quality, architecture, perf
4. **Minor Issues** — style, docs, micro-opts
5. **Recommendations** — refactors sugeridos
6. **Approval Status** — listo para merge / requiere cambios
7. **Obstacles Encountered** — dependencias, env quirks, workarounds

Sé conciso. Cita file:line cuando sea posible.
"""


if __name__ == "__main__":
    mcp.run()
