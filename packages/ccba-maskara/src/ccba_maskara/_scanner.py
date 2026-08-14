"""MaskaraScanner - Central Deep Module for secret detection and redaction."""

from __future__ import annotations

import hashlib
import os
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
        """Determine if filename pattern looks like session/logs text."""
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
        ]:
            return True
        if name.startswith(".env"):
            return True
        keywords = ["session", "conversation", "transcript", "history"]
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

    def scan_text(
        self, content: str, filepath: str = "", agent: str = "", use_llm: bool = False
    ) -> list[dict[str, Any]]:
        """Scan string content with regex pattern suite."""
        findings: list[dict[str, Any]] = []

        for rule_id, rule_spec in REGEX_PATTERNS.items():
            pattern = rule_spec["pattern"]
            for match in pattern.finditer(content):
                if rule_id == "env-secret":
                    val = match.group(1)
                    start, end = match.start(1), match.end(1)
                else:
                    val = match.group(0)
                    start, end = match.start(), match.end()

                if val in SAFE_STRINGS or "MASKARA_REDACTED" in val:
                    continue

                line, col = self.line_and_column(content, start)
                finding = {
                    "rule_id": rule_id,
                    "rule_name": rule_spec["name"],
                    "severity": rule_spec["severity"],
                    "agent": agent,
                    "file": filepath,
                    "line": line,
                    "column": col,
                    "start": start,
                    "end": end,
                    "preview": self.mask_value(val),
                    "sha256": hashlib.sha256(val.encode("utf-8")).hexdigest(),
                    "redaction": f"[MASKARA_REDACTED:{rule_id}]",
                }

                if use_llm:
                    context_str = self.extract_context(content, start, end)
                    if not self.ask_llm_gateway(finding, context_str):
                        continue

                findings.append(finding)

        findings.sort(key=lambda x: (x["file"], x["start"]))
        filtered: list[dict[str, Any]] = []
        for f in findings:
            overlap = False
            for k in filtered:
                if f["file"] == k["file"] and f["start"] < k["end"] and k["start"] < f["end"]:
                    overlap = True
                    break
            if not overlap:
                filtered.append(f)

        return filtered

    def redact_text(self, content: str, agent: str = "text") -> str:
        """Scan and redact secret patterns in text content string."""
        findings = self.scan_text(content, filepath="string", agent=agent)
        if not findings:
            return content

        raw_bytes = content.encode("utf-8")
        redacted_bytes, _ = self.apply_raw_redactions(raw_bytes, findings)
        return redacted_bytes.decode("utf-8", errors="ignore")

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

        ignore_dirs = {
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
        }

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
            lines.append("## Scan Targets\n")
            lines.append("| Agent | Root |")
            lines.append("|---|---|")
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

        rule_counts: dict[str, int] = {}
        for f in result["findings"]:
            rule_counts[f["rule_name"]] = rule_counts.get(f["rule_name"], 0) + 1
        sorted_rules = sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))

        lines.append("## Summary By Rule\n")
        lines.append("| Rule | Count |")
        lines.append("|---|---:|")
        for name, cnt in sorted_rules:
            lines.append(f"| {name} | {cnt} |")
        lines.append("")

        lines.append("## Findings\n")
        lines.append("| Agent | File | Line | Rule | Severity | Masked Preview | SHA-256 |")
        lines.append("|---|---|---:|---|---|---|---|")
        for f in result["findings"]:
            clean_file = f["file"].replace("|", "\\|")
            clean_rule = f["rule_name"].replace("|", "\\|")
            lines.append(
                f"| `{f['agent']}` | `{clean_file}` | {f['line']} | "
                f"{clean_rule} | `{f['severity']}` | `{f['preview']}` | `{f['sha256'][:12]}` |"
            )
        lines.append("")
        lines.append("## Rotation Guidance\n")
        lines.append(
            "Rotate every credential listed above. Redaction removes local copies from agent logs, "
            "but it cannot revoke credentials already shared with a provider or remote service.\n"
        )

        if files := redact_summary.get("files"):
            lines.append("## Redaction Backups\n")
            for f in files:
                lines.append(f"- `{f['path']}` -> backup `{f['backup_path']}`")

        return "\n".join(lines)

    def install_guardrails(self, agent_name: str, dry_run: bool = False) -> list[dict[str, str]]:
        """Install guardrail instructions and hooks for target agent."""
        import shutil

        changes: list[dict[str, str]] = []
        norm = self.normalize_agent_name(agent_name)
        if norm in ["auto", "all"]:
            target_agents = []
            for candidate in AGENT_SPECS:
                spec = AGENT_SPECS[candidate]
                for path in self.get_default_roots(
                    spec["dot_dir"], spec["app_name"], spec["xdg_name"]
                ):
                    if path.is_dir():
                        target_agents.append(candidate)
                        break
            if not target_agents:
                target_agents = ["claude", "codex"]
        else:
            if norm not in AGENT_SPECS:
                raise ValueError(f"Unsupported guardrails agent: {agent_name}")
            target_agents = [norm]

        guardrail_content = """# Maskara Privacy Guardrails

Never print, quote, summarize, or store raw secrets from `.env` files, shell
history, cloud CLIs, keychains, password managers, session logs, or agent logs.
"""
        skill_content = """---
name: maskara-privacy
description: Prevent accidental disclosure of secrets in coding-agent sessions and route cleanup through maskara.
---
# Maskara Privacy Skill
"""
        hook_content = """$payload = if ($args.Count -gt 0) { $args -join " " } else { [Console]::In.ReadToEnd() }
$lower = $payload.ToLowerInvariant()
$blocked = @(".env", "printenv", "authorization:", "bearer ", "private key", "secret")
foreach ($term in $blocked) {
  if ($lower.Contains($term)) {
    Write-Error "maskara guardrails: command may expose secrets."
    exit 2
  }
}
exit 0
"""
        for agent in target_agents:
            spec = AGENT_SPECS[agent]
            roots = self.get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
            if not roots:
                continue
            primary_root = roots[0]

            if agent == "claude":
                plans = [
                    {
                        "path": primary_root / "CLAUDE.md",
                        "action": "append",
                        "content": guardrail_content,
                    },
                    {
                        "path": primary_root / "skills" / "maskara-privacy" / "SKILL.md",
                        "action": "write",
                        "content": skill_content,
                    },
                    {
                        "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                        "action": "write",
                        "content": hook_content,
                    },
                ]
            else:
                plans = [
                    {
                        "path": primary_root / "maskara-guardrails.md",
                        "action": "append",
                        "content": guardrail_content,
                    },
                    {
                        "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                        "action": "write",
                        "content": hook_content,
                    },
                ]

            for plan in plans:
                path = Path(plan["path"])
                action = plan["action"]
                content = plan["content"]
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
