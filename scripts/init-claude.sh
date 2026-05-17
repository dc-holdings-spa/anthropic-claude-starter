#!/usr/bin/env bash
# Resuelve $PWD en settings.example.json → settings.local.json (gitignored)
# Run después de clonar el repo.
#
# Razón: hook commands con path absolute (mitigates MITRE T1574.007 / OWASP binary planting)
# pero queremos compartir settings.example.json en git con $PWD placeholder.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

EXAMPLE="$ROOT/.claude/settings.example.json"
LOCAL="$ROOT/.claude/settings.local.json"

if [ ! -f "$EXAMPLE" ]; then
  echo "ERROR: $EXAMPLE not found"
  exit 1
fi

# Reemplazar $PWD literal por path absoluto del repo
sed "s|\$PWD|$ROOT|g" "$EXAMPLE" > "$LOCAL"

echo "[+] settings.local.json generado:"
echo "    $LOCAL"
echo "    (gitignored — local a tu máquina)"
echo ""
echo "[+] Hooks instalados:"
grep -oE '"command": "[^"]*"' "$LOCAL" | head -5
echo ""
echo "Reinicia Claude Code para cargar los hooks."
