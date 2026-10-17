"""MaskaraScanner - Central Deep Module for secret detection and redaction."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._locator import (
    AGENT_SPECS,
    get_default_roots,
    normalize_agent_name,
    resolve_targets,
)
from ._redactor import (
    apply_raw_redactions,
    backup_and_write,
)
from ._redactor import (
    redact_findings as _redact_findings,
)
from ._rules import REGEX_PATTERNS, SAFE_STRINGS

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "target",
        "dist",
        "build",
        ".next",
        "__pycache__",
        ".md",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".import_linter_cache",
    }
)


_KNOWN_TOKEN_METRICS: frozenset[str] = frozenset(
    {
        "tokens",
        "input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "cached_read_tokens",
        "total_tokens",
        "total_fleet_tokens",
        "fleet_tokens",
        "max_tokens",
        "prompt_tokens",
        "completion_tokens",
        "blocker_tokens",
        "all_tokens",
        "token_count",
        "token_limit",
        "token_budget",
        "token_tracker",
        "max_output_tokens",
    }
)


_COLLECTION_PREFIXES: tuple[str, ...] = (
    "[",
    "set[",
    "set(",
    "frozenset[",
    "frozenset(",
    "list[",
    "list(",
    "dict[",
    "dict(",
    "tuple[",
)


def is_safe_or_template(val: str, key_hint: str = "") -> bool:
    """Check if value is a known safe string, template expression, or non-sensitive numeric value."""
    if val in SAFE_STRINGS or "MASKARA_REDACTED" in val:
        return True
    stripped = val.strip()
    if stripped.startswith(("${", "$(", "{{", "<%", "<#")):
        return True
    if stripped.startswith("{") and not stripped.startswith(('{"', "{'")):
        if stripped.endswith("}") or re.match(r"^\{[A-Za-z_][A-Za-z0-9_.]*[:,\s]", stripped):
            return True
    if stripped.startswith(
        ("args.", "self.", "params.", "os.environ/", "os.environ.", "os.getenv", "env/")
    ):
        return True
    if stripped.isdigit():
        key_lower = key_hint.lower()
        sensitive_terms = ("password", "passwd", "pwd", "secret", "credential", "pin")
        return not any(term in key_lower for term in sensitive_terms)
    lower = stripped.lower()
    if (
        lower.startswith(("your_", "your-", "dummy", "sample", "example", "mock"))
        or lower.endswith(("_placeholder", "-placeholder", "_here", "-here"))
        or "change_me" in lower
        or "placeholder" in lower
    ):
        return True
    # COND-MASKARA-TOKEN: Ignore explicit LLM token counter metrics and Python type annotations
    key_clean = key_hint.split("=")[0].split(":")[0].strip().lower()
    key_stem = key_clean.split(".")[-1].strip()
    if (
        key_stem in _KNOWN_TOKEN_METRICS
        or key_clean in _KNOWN_TOKEN_METRICS
        or key_stem.endswith("tokens")
        or "_tokens_" in key_stem
    ):
        return True
    return stripped.startswith(_COLLECTION_PREFIXES)


class MaskaraScanner:
    """Deep module hiding secret regex matching, file scanning, redaction, and reporting.

    Provides a clean interface:
    - `scan_text(content, ...)`
    - `redact_text(content, ...)`
    - `scan_file(agent, path, ...)`
    - `perform_scan(targets, ...)`
    - `redact_findings(scan_result)`
    - `is_binary(filepath)`
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize MaskaraScanner with optional project root."""
        if project_root is None:
            # Default to 4 levels up if inside package, or fallback
            project_root = Path(__file__).resolve().parents[4]
        self.project_root = project_root

    def normalize_agent_name(self, name: str) -> str:
        """Normalize agent name to canonical key."""
        return normalize_agent_name(name)

    def get_default_roots(self, dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
        """Retrieve system-specific default log paths."""
        return get_default_roots(dot_dir, app_name, xdg_name)

    def resolve_targets(
        self, agent_name: str, custom_root: str | None = None
    ) -> list[dict[str, Any]]:
        """Resolve which target directories/agents to scan."""
        return resolve_targets(agent_name, custom_root)

    def looks_like_session_text(self, path: Path) -> bool:
        """Determine if filename pattern looks like session/logs text or config/secret file."""
        name = path.name.lower()
        ext = path.suffix.lower()
        if ext in [
            ".json",
            ".jsonl",
            ".md",
            ".txt",
            ".log",
            ".yaml",
            ".yml",
            ".toml",
            ".env",
            ".xml",
            ".bak",
            ".conf",
            ".ini",
            ".cfg",
            ".properties",
            ".sh",
            ".bash",
            ".zsh",
        ]:
            return True
        if name.startswith(".env") or ".env." in name or name.endswith(".env"):
            return True
        keywords = ["session", "conversation", "transcript", "history", "secret", "credential"]
        return any(kw in name for kw in keywords)

    def is_binary(self, filepath: Path) -> bool:
        """Check if file is binary by searching for null bytes."""
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(8192)
                return b"\x00" in chunk
        except OSError:
            return True

    def line_and_column(self, content: str, offset: int) -> tuple[int, int]:
        """Calculate 1-indexed line and column numbers for character offset."""
        lines = content[:offset].split("\n")
        return len(lines), len(lines[-1]) + 1

    def mask_value(self, val: str) -> str:
        """Mask sensitive string value leaving terminal characters."""
        clean = val.replace("\r", "").replace("\n", "\\n")
        if len(clean) <= 8:
            return "***"
        return f"{clean[:4]}...{clean[-4:]}"

    def ask_llm_gateway(self, finding: dict[str, Any], context: str) -> bool:
        """Query AI Gateway to double-verify finding."""
        try:
            from ccba_ai import ai
        except ImportError:
            return True

        prompt = f"""You are a security auditor.
Analyze the following context from an agent session log and determine if the detected finding is an actual, live, active secret/credential/API key, OR if it is just a mock/sample/dummy value (e.g. 'your_key_here', 'sk-proj-XXXX', 'AIza_test').

Detected Type: {finding["rule_name"]}
Detected Value (Masked): {finding["preview"]}

Context:
```
{context}
```

Is this a real sensitive credential that must be rotated? Reply with ONLY 'YES' or 'NO'."""
        try:
            response = ai.chat(prompt)
            return "YES" in response.upper()
        except Exception as e:
            print(
                f"[Warning] AI Gateway validation failed, defaulting to True: {e}", file=sys.stderr
            )
            return True

    def extract_context(self, content: str, start_offset: int, end_offset: int) -> str:
        """Extract context lines surrounding a finding."""
        before = content[:start_offset].split("\n")[-3:]
        after = content[end_offset:].split("\n")[:3]
        middle = content[start_offset:end_offset]
        return "\n".join(before + [middle] + after)

    def _build_finding_record(
        self,
        content: str,
        rule_id: str,
        rule_spec: dict[str, Any],
        val: str,
        start: int,
        end: int,
        filepath: str,
        agent: str,
    ) -> dict[str, Any]:
        """Construct a structured finding dictionary for a matched secret."""
        line, col = self.line_and_column(content, start)
        byte_start = len(content[:start].encode("utf-8"))
        byte_end = byte_start + len(val.encode("utf-8"))
        return {
            "rule_id": rule_id,
            "rule_name": rule_spec["name"],
            "severity": rule_spec["severity"],
            "agent": agent,
            "file": filepath,
            "line": line,
            "column": col,
            "start": start,
            "end": end,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "preview": self.mask_value(val),
            "sha256": hashlib.sha256(val.encode("utf-8")).hexdigest(),
            "redaction": f"[MASKARA_REDACTED:{rule_id}]",
        }

    def scan_text(
        self, content: str, filepath: str = "", agent: str = "", use_llm: bool = False
    ) -> list[dict[str, Any]]:
        """Scan string content with regex pattern suite."""
        findings: list[dict[str, Any]] = []
        for rule_id, rule_spec in REGEX_PATTERNS.items():
            for match in rule_spec["pattern"].finditer(content):
                if rule_id == "env-secret":
                    val, start, end = match.group(1), match.start(1), match.end(1)
                    if is_safe_or_template(val, key_hint=match.group(0)):
                        continue
                else:
                    val, start, end = match.group(0), match.start(), match.end()
                if val in SAFE_STRINGS or "MASKARA_REDACTED" in val:
                    continue
                finding = self._build_finding_record(
                    content, rule_id, rule_spec, val, start, end, filepath, agent
                )
                if use_llm and not self.ask_llm_gateway(
                    finding, self.extract_context(content, start, end)
                ):
                    continue
                findings.append(finding)

        findings.sort(key=lambda x: (x["file"], x["start"]))
        filtered: list[dict[str, Any]] = []
        for f in findings:
            if not any(
                f["file"] == k["file"] and f["start"] < k["end"] and k["start"] < f["end"]
                for k in filtered
            ):
                filtered.append(f)
        return filtered

    def redact_text(self, content: str, agent: str = "text") -> str:
        """Scan and redact secret patterns in text content string."""
        findings = self.scan_text(content, filepath="string", agent=agent)
        if not findings:
            return content

        res = content
        for f in sorted(findings, key=lambda x: x["start"], reverse=True):
            s, e = f["start"], f["end"]
            res = res[:s] + f["redaction"] + res[e:]
        return res

    def apply_raw_redactions(
        self, original: bytes, findings: list[dict[str, Any]]
    ) -> tuple[bytes, int]:
        """Delegate to _redactor.apply_raw_redactions."""
        return apply_raw_redactions(original, findings)

    def backup_and_write(self, path: Path, original: bytes, rewritten: bytes) -> str:
        """Delegate to _redactor.backup_and_write."""
        return backup_and_write(path, original, rewritten)

    def redact_findings(self, scan_result: dict[str, Any]) -> dict[str, Any]:
        """Execute redaction on findings."""
        return _redact_findings(scan_result)

    def scan_file(
        self, agent: str, path: Path, use_llm: bool = False
    ) -> tuple[list[dict[str, Any]], int, int]:
        """Perform scanning process on a single file."""
        try:
            if path.is_symlink() or path.is_dir():
                return [], 0, 1
            if path.stat().st_size > MAX_FILE_SIZE or not self.looks_like_session_text(path):
                return [], 0, 1
            if self.is_binary(path):
                return [], 0, 1

            content = path.read_text(encoding="utf-8", errors="ignore")
            findings = self.scan_text(content, str(path), agent, use_llm)
            return findings, 1, 0
        except OSError:
            return [], 0, 1

    def perform_scan(self, targets: list[dict[str, Any]], use_llm: bool = False) -> dict[str, Any]:
        """Perform scanning across resolved targets."""
        findings: list[dict[str, Any]] = []
        warnings: list[str] = []
        scanned_count = 0
        skipped_count = 0

        ignore_dirs = set(DEFAULT_IGNORE_DIRS)

        for target in targets:
            root = Path(target["root"])
            agent = target["agent"]
            if not root.exists():
                warnings.append(f"missing root: {root}")
                continue

            if root.is_file():
                f, sc, sk = self.scan_file(agent, root, use_llm)
                findings.extend(f)
                scanned_count += sc
                skipped_count += sk
                continue

            for root_dir, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs]
                for file in files:
                    filepath = Path(root_dir) / file
                    f, sc, sk = self.scan_file(agent, filepath, use_llm)
                    findings.extend(f)
                    scanned_count += sc
                    skipped_count += sk

        findings.sort(key=lambda x: (x["file"], x["start"]))
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "targets": [{"agent": t["agent"], "root": str(t["root"])} for t in targets],
            "findings": findings,
            "warnings": warnings,
            "files_scanned": scanned_count,
            "files_skipped": skipped_count,
        }

    @staticmethod
    def _append_findings_markdown(
        lines: list[str], findings: list[dict[str, Any]], redact_summary: dict[str, Any]
    ) -> None:
        """Append rule summary, findings table, and backup details to Markdown report lines."""
        rule_counts: dict[str, int] = {}
        for f in findings:
            rule_counts[f["rule_name"]] = rule_counts.get(f["rule_name"], 0) + 1
        sorted_rules = sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))
        lines.extend(["## Summary By Rule\n", "| Rule | Count |", "|---|---:|"])
        for name, cnt in sorted_rules:
            lines.append(f"| {name} | {cnt} |")
        lines.extend(
            [
                "",
                "## Findings\n",
                "| Agent | File | Line | Rule | Severity | Masked Preview | SHA-256 |",
                "|---|---|---:|---|---|---|---|",
            ]
        )
        for f in findings:
            clean_file = f["file"].replace("|", "\\|")
            clean_rule = f["rule_name"].replace("|", "\\|")
            lines.append(
                f"| `{f['agent']}` | `{clean_file}` | {f['line']} | "
                f"{clean_rule} | `{f['severity']}` | `{f['preview']}` | `{f['sha256'][:12]}` |"
            )
        lines.extend(
            [
                "",
                "## Rotation Guidance\n",
                "Rotate every credential listed above. Redaction removes local copies from agent logs, "
                "but it cannot revoke credentials already shared with a provider or remote service.\n",
            ]
        )
        if files := redact_summary.get("files"):
            lines.append("## Redaction Backups\n")
            for f in files:
                lines.append(f"- `{f['path']}` -> backup `{f['backup_path']}`")

    def generate_markdown(self, result: dict[str, Any], redact_summary: dict[str, Any]) -> str:
        """Generate Markdown report contents."""
        lines = [
            "# Maskara Secret Exposure Report\n",
            f"- Generated: `{result['generated_at']}`",
            f"- Files scanned: `{result['files_scanned']}`",
            f"- Files skipped: `{result['files_skipped']}`",
            f"- Findings: `{len(result['findings'])}`",
            f"- Redacted: `{redact_summary['replaced']}`\n",
        ]
        if targets := result.get("targets"):
            lines.extend(["## Scan Targets\n", "| Agent | Root |", "|---|---|"])
            for t in targets:
                clean_root = t["root"].replace("|", "\\|")
                lines.append(f"| `{t['agent']}` | `{clean_root}` |")
            lines.append("")
        if warnings := result.get("warnings"):
            lines.append("## Warnings\n")
            for w in warnings:
                lines.append(f"- {w}")
            lines.append("")
        if not result["findings"]:
            lines.append("## Findings\n\nNo sensitive values detected.")
            return "\n".join(lines)
        self._append_findings_markdown(lines, result["findings"], redact_summary)
        return "\n".join(lines)

    def _resolve_guardrail_agents(self, agent_name: str) -> list[str]:
        """Resolve list of target agent identifiers for guardrail installation."""
        norm = self.normalize_agent_name(agent_name)
        if norm in ["auto", "all"]:
            target_agents: list[str] = []
            for candidate, spec in AGENT_SPECS.items():
                if any(
                    p.is_dir()
                    for p in self.get_default_roots(
                        spec["dot_dir"], spec["app_name"], spec["xdg_name"]
                    )
                ):
                    target_agents.append(candidate)
            return target_agents or ["claude", "codex"]
        if norm not in AGENT_SPECS:
            raise ValueError(f"Unsupported guardrails agent: {agent_name}")
        return [norm]

    @staticmethod
    def _build_guardrail_plans(agent: str, primary_root: Path) -> list[dict[str, Any]]:
        """Construct guardrail file write/append plans for a single agent root."""
        guardrail_content = (
            "# Maskara Privacy Guardrails\n\n"
            "Never print, quote, summarize, or store raw secrets from `.env` files, shell\n"
            "history, cloud CLIs, keychains, password managers, session logs, or agent logs.\n"
        )
        skill_content = (
            "---\nname: maskara-privacy\n"
            "description: Prevent accidental disclosure of secrets in coding-agent sessions and route cleanup through maskara.\n"
            "---\n# Maskara Privacy Skill\n"
        )
        hook_content = (
            '$payload = if ($args.Count -gt 0) { $args -join " " } else { [Console]::In.ReadToEnd() }\n'
            "$lower = $payload.ToLowerInvariant()\n"
            '$blocked = @(".env", "printenv", "authorization:", "bearer ", "private key", "secret")\n'
            "foreach ($term in $blocked) {\n"
            '  if ($lower.Contains($term)) { Write-Error "maskara guardrails: command may expose secrets."; exit 2 }\n'
            "}\nexit 0\n"
        )
        doc_name = "CLAUDE.md" if agent == "claude" else "maskara-guardrails.md"
        plans: list[dict[str, Any]] = [
            {"path": primary_root / doc_name, "action": "append", "content": guardrail_content},
            {
                "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                "action": "write",
                "content": hook_content,
            },
        ]
        if agent == "claude":
            plans.insert(
                1,
                {
                    "path": primary_root / "skills" / "maskara-privacy" / "SKILL.md",
                    "action": "write",
                    "content": skill_content,
                },
            )
        return plans

    def install_guardrails(self, agent_name: str, dry_run: bool = False) -> list[dict[str, str]]:
        """Install guardrail instructions and hooks for target agent."""
        import shutil

        changes: list[dict[str, str]] = []
        for agent in self._resolve_guardrail_agents(agent_name):
            spec = AGENT_SPECS[agent]
            roots = self.get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
            if not roots:
                continue
            for plan in self._build_guardrail_plans(agent, roots[0]):
                path = Path(str(plan["path"]))
                action = str(plan["action"])
                content = str(plan["content"])
                backup_path = ""
                if not dry_run:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if action == "append" and path.exists():
                        orig = path.read_text(encoding="utf-8", errors="ignore")
                        if "MASKARA-GUARDRAILS" not in orig:
                            bp = path.with_suffix(f"{path.suffix}.maskara.bak")
                            shutil.copy2(path, bp)
                            backup_path = str(bp)
                            with open(path, "a", encoding="utf-8") as f:
                                f.write(f"\n\n{content}")
                    else:
                        if path.exists():
                            bp = path.with_suffix(f"{path.suffix}.maskara.bak")
                            shutil.copy2(path, bp)
                            backup_path = str(bp)
                        path.write_text(content, encoding="utf-8")
                changes.append({"path": str(path), "action": action, "backup_path": backup_path})
        return changes

    def run_cli(self, args_list: list[str] | None = None) -> int:
        """CLI runner for Maskara (delegating to cli.py)."""
        from .cli import run_cli

        return run_cli(args_list, scanner=self)
