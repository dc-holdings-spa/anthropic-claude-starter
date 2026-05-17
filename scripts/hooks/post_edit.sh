#!/usr/bin/env bash
# PostToolUse hook: type-check + format si aplica.
# Exit 0 = OK, exit 2 = devuelve feedback a Claude para que arregle.

set -e
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))" 2>/dev/null || echo "")

if [ -z "$FILE" ]; then exit 0; fi

case "$FILE" in
    *.py)
        # ruff format + check si está instalado
        if command -v ruff &>/dev/null; then
            ruff format "$FILE" >/dev/null 2>&1 || true
            if ! ruff check "$FILE" 2>&1; then
                echo "ruff check found issues in $FILE — please fix"
                exit 2
            fi
        fi
        ;;
    *.ts|*.tsx)
        # tsc --noEmit si tsconfig.json existe
        if [ -f "tsconfig.json" ] && command -v npx &>/dev/null; then
            if ! npx tsc --noEmit 2>&1; then
                echo "TypeScript errors detected — fix before continuing"
                exit 2
            fi
        fi
        ;;
esac

exit 0
