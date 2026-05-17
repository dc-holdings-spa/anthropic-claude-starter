.PHONY: help install init e2e e2e-full lint format mcp-dev anatomist-lint clean

help:
	@echo "make install        — pip install -e .[dev]"
	@echo "make init           — resolve \$$PWD en .claude/settings.local.json"
	@echo "make e2e            — tier-1 tests (cero tokens)"
	@echo "make e2e-full       — tier-2 tests (burns LLM tokens)"
	@echo "make lint           — ruff check + anatomist-lint"
	@echo "make format         — ruff format"
	@echo "make mcp-dev        — abre MCP Inspector para demo server"
	@echo "make anatomist-lint — solo anti-pattern check"
	@echo "make clean          — remove build artifacts"

install:
	pip install -e ".[dev]"

init:
	bash scripts/init-claude.sh
	chmod +x scripts/hooks/*.sh scripts/hooks/*.js 2>/dev/null || true

e2e:
	pytest tests/tier1 -v -m tier1

e2e-full:
	pytest tests/tier2 -v -m tier2

lint:
	ruff check src/ tests/ scripts/
	python scripts/anatomist-lint.py .

format:
	ruff format src/ tests/ scripts/

mcp-dev:
	mcp dev src/mcp_servers/demo.py

anatomist-lint:
	python scripts/anatomist-lint.py .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .ruff_cache/ .mypy_cache/
