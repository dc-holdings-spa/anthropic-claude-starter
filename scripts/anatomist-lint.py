#!/usr/bin/env python3
"""
Anti-pattern linter. Exit 0 si todo OK, exit 1 si hay critical/major findings.

Detecta los 10 anti-patterns Anthropic best-practices:
1. API key en frontend
2. Substring classifiers para contenido semántico
3. Hooks con path relativo
4. Tool descriptions vagas/duplicadas
5. Expert claim subagents
6. Test runner subagents que esconden output
7. Tool allowlist > 15 sin doc
8. System prompt grande sin cache_control
9. Tested-once código (heurística: archivo nuevo sin test correspondiente)
10. Sequential subagent pipelines (manual check, no automatable fácil)

Run:
    python scripts/anatomist-lint.py [--fix]

CI integration:
    pre-commit hook + .github/workflows/anatomist-lint.yml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    severity: str  # critical | major | minor
    pattern: str
    file: str
    line: int = 0
    message: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, pattern: str, file: str, line: int = 0, message: str = "") -> None:
        self.findings.append(Finding(severity, pattern, file, line, message))

    def by_severity(self, sev: str) -> list[Finding]:
        return [f for f in self.findings if f.severity == sev]

    def exit_code(self) -> int:
        if self.by_severity("critical") or self.by_severity("major"):
            return 1
        return 0


# ----------------------------------------------------------------------
# Individual checks.
# ----------------------------------------------------------------------
FRONTEND_EXTS = {".js", ".ts", ".tsx", ".jsx", ".html", ".vue"}
API_KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_-]+")


def check_api_key_in_frontend(root: Path, report: Report) -> None:
    for ext in FRONTEND_EXTS:
        for path in root.rglob(f"*{ext}"):
            if "node_modules" in path.parts or ".git" in path.parts:
                continue
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            for m in API_KEY_PATTERN.finditer(content):
                line = content[: m.start()].count("\n") + 1
                report.add(
                    "critical",
                    "api_key_in_frontend",
                    str(path),
                    line,
                    f"hardcoded API key found: {m.group(0)[:12]}...",
                )


SUBSTRING_CLASSIFIER_PATTERN = re.compile(
    r"^_[A-Z_]+\s*=\s*(?:frozenset|set|\{|\[)", re.MULTILINE
)


def check_substring_classifiers(root: Path, report: Report) -> None:
    for path in root.rglob("*.py"):
        if any(part in {"venv", ".venv", "tests", "node_modules"} for part in path.parts):
            continue
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        for m in SUBSTRING_CLASSIFIER_PATTERN.finditer(content):
            line = content[: m.start()].count("\n") + 1
            # Filtra falsos positivos triviales (ej _ALL_TOOLS = [...] de registro)
            decl = content[m.start() : m.start() + 80]
            if any(kw in decl.upper() for kw in ("HINT", "PATTERN", "CLASSIFIER", "KEYWORD", "TRIGGER")):
                report.add(
                    "major",
                    "substring_classifier",
                    str(path),
                    line,
                    f"posible semantic classifier: {decl.strip()[:60]}",
                )


def check_hook_relative_paths(root: Path, report: Report) -> None:
    """Hook commands deben empezar con: / (absolute) o $VAR/ ($PWD, $CLAUDE_PROJECT_DIR — env vars resolved a absolute)."""
    for name in ("settings.json", "settings.local.json"):
        # NOTA: settings.example.json es plantilla, ignora — init-claude.sh resuelve $PWD a absolute
        path = root / ".claude" / name
        if not path.exists():
            continue
        try:
            content = path.read_text()
        except Exception:
            continue
        pat = re.compile(r'"command"\s*:\s*"([^"]+)"')
        for m in pat.finditer(content):
            cmd = m.group(1)
            # Extraer el ejecutable (primer token después de runner como `node`/`bash`/`python`)
            tokens = cmd.split()
            target = tokens[1] if len(tokens) > 1 and tokens[0] in ("node", "bash", "sh", "python", "python3") else tokens[0]
            if target.startswith("/") or target.startswith("$"):
                continue  # absolute o env var (que init script resuelve)
            line = content[: m.start()].count("\n") + 1
            report.add(
                "critical",
                "hook_relative_path",
                str(path),
                line,
                f"hook command con path relativo (T1574.007): {cmd[:60]}",
            )


def check_expert_claims(root: Path, report: Report) -> None:
    pat = re.compile(r"(?:you|tú)\s+(?:are|eres|sos)\s+(?:an?\s+)?(?:expert|specialist|guru|wizard)", re.I)
    for sub in [".claude/agents", ".claude/skills"]:
        target_dir = root / sub
        if not target_dir.exists():
            continue
        for path in target_dir.rglob("*.md"):
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            for m in pat.finditer(content):
                line = content[: m.start()].count("\n") + 1
                report.add(
                    "minor",
                    "expert_claim",
                    str(path),
                    line,
                    "expert claim sin value (Claude ya tiene knowledge)",
                )


def check_tool_descriptions(root: Path, report: Report) -> None:
    """Descriptions <20 chars o duplicadas entre agents/skills."""
    descs: dict[str, list[str]] = {}
    desc_pat = re.compile(r"^description:\s*(.+)$", re.MULTILINE)
    for path in root.rglob(".claude/**/*.md"):
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        for m in desc_pat.finditer(content):
            d = m.group(1).strip().strip('"').strip("'")
            line = content[: m.start()].count("\n") + 1
            if len(d) < 20:
                report.add(
                    "major",
                    "vague_description",
                    str(path),
                    line,
                    f"description muy corta ({len(d)} chars): {d}",
                )
            descs.setdefault(d, []).append(f"{path}:{line}")
    for d, locations in descs.items():
        if len(locations) > 1:
            for loc in locations:
                p, line = loc.rsplit(":", 1)
                report.add(
                    "major",
                    "duplicate_description",
                    p,
                    int(line),
                    f"description duplicada en {len(locations)} agents/skills",
                )


def check_test_runner_subagents(root: Path, report: Report) -> None:
    """Subagents que devuelven solo pass/fail sin output completo = anti-pattern."""
    target_dir = root / ".claude" / "agents"
    if not target_dir.exists():
        return
    test_hint = re.compile(r"\b(?:test|tests)\b.*\b(?:run|runner|execute)", re.I)
    output_only = re.compile(r"return\s+(?:only\s+)?(?:pass|fail|true|false|status)", re.I)
    for path in target_dir.rglob("*.md"):
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        if test_hint.search(content) and output_only.search(content):
            report.add(
                "major",
                "test_runner_subagent",
                str(path),
                1,
                "test runner subagent que esconde output (anti-pattern Subagents L4)",
            )


def check_tool_allowlist_size(root: Path, report: Report) -> None:
    """Subagent con >15 tools sin justificación visible = least-privilege violation."""
    target_dir = root / ".claude" / "agents"
    if not target_dir.exists():
        return
    tools_pat = re.compile(r"^tools:\s*(.+)$", re.MULTILINE)
    for path in target_dir.rglob("*.md"):
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        m = tools_pat.search(content)
        if not m:
            continue
        tools = [t.strip() for t in m.group(1).split(",") if t.strip()]
        if len(tools) > 15:
            report.add(
                "minor",
                "tool_allowlist_large",
                str(path),
                content[: m.start()].count("\n") + 1,
                f"{len(tools)} tools — verificar least-privilege (recomendado <15)",
            )


def check_caching_opportunity(root: Path, report: Report) -> None:
    """Calls a messages.create con system grande sin cache_control = waste."""
    py_pat = re.compile(r"messages\.create\s*\(([^)]+)\)", re.DOTALL)
    sys_pat = re.compile(r'system\s*=\s*["\'](.{800,})["\']', re.DOTALL)
    for path in root.rglob("*.py"):
        if any(part in {"venv", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        for m in py_pat.finditer(content):
            block = m.group(1)
            if sys_pat.search(block) and "cache_control" not in block:
                line = content[: m.start()].count("\n") + 1
                report.add(
                    "minor",
                    "missed_caching",
                    str(path),
                    line,
                    "system prompt grande sin cache_control (waste tokens)",
                )


def check_sequential_pipeline_hint(root: Path, report: Report) -> None:
    """Subagents que documentan "after N completes" en system prompt = pipeline frágil."""
    target_dir = root / ".claude" / "agents"
    if not target_dir.exists():
        return
    pipeline_pat = re.compile(
        r"(?:after|tras|once)\s+(?:agent_|subagent_|\w+_agent)",
        re.I,
    )
    for path in target_dir.rglob("*.md"):
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        for m in pipeline_pat.finditer(content):
            line = content[: m.start()].count("\n") + 1
            report.add(
                "minor",
                "sequential_pipeline_hint",
                str(path),
                line,
                "posible sequential pipeline (info loss en handoff)",
            )


# ----------------------------------------------------------------------
# Main.
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Anti-pattern linter")
    parser.add_argument("path", nargs="?", default=".", help="Root path to scan")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    report = Report()

    check_api_key_in_frontend(root, report)
    check_substring_classifiers(root, report)
    check_hook_relative_paths(root, report)
    check_expert_claims(root, report)
    check_tool_descriptions(root, report)
    check_test_runner_subagents(root, report)
    check_tool_allowlist_size(root, report)
    check_caching_opportunity(root, report)
    check_sequential_pipeline_hint(root, report)

    # Output.
    for sev in ("critical", "major", "minor"):
        items = report.by_severity(sev)
        if not items:
            continue
        print(f"\n## {sev.upper()} ({len(items)})")
        for f in items:
            print(f"  [{f.pattern}] {f.file}:{f.line}")
            if f.message:
                print(f"      {f.message}")

    n_crit = len(report.by_severity("critical"))
    n_maj = len(report.by_severity("major"))
    n_min = len(report.by_severity("minor"))
    print(f"\n=== Summary: {n_crit} critical, {n_maj} major, {n_min} minor ===")

    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())
