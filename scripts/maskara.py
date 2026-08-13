#!/usr/bin/env python3
"""CCBA Maskara - Unified Deep Module for Security Scanning & PII Redaction.

Hides regex pattern matching, agent log path resolution, AI Gateway double-checks,
and binary/structured format redaction logic behind a clean `MaskaraScanner` surface:
- `scan_text(content)`
- `redact_text(content)`
- `scan_workspace(root, agent)`
- `redact_workspace(root, agent)`
- `run_cli(args_list)`

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Standard agent profiles and paths configuration
AGENT_SPECS: dict[str, dict[str, str]] = {
    "claude": {"dot_dir": ".claude/projects", "app_name": "Claude", "xdg_name": "claude"},
    "codex": {"dot_dir": ".codex/sessions", "app_name": "Codex", "xdg_name": "codex"},
    "cursor": {"dot_dir": ".cursor", "app_name": "Cursor", "xdg_name": "cursor"},
    "opencode": {"dot_dir": ".opencode", "app_name": "opencode", "xdg_name": "opencode"},
    "antigravity": {
        "dot_dir": ".antigravity",
        "app_name": "Antigravity",
        "xdg_name": "antigravity",
    },
    "kimi": {"dot_dir": ".kimi", "app_name": "Kimi", "xdg_name": "kimi"},
    "droid": {"dot_dir": ".droid", "app_name": "Droid", "xdg_name": "droid"},
    "gemini": {"dot_dir": ".gemini", "app_name": "Gemini", "xdg_name": "gemini"},
    "github-copilot": {
        "dot_dir": ".github-copilot",
        "app_name": "GitHub Copilot",
        "xdg_name": "github-copilot",
    },
    "hermes": {"dot_dir": ".hermes", "app_name": "Hermes Agent", "xdg_name": "hermes"},
    "openclaw": {"dot_dir": ".openclaw", "app_name": "OpenClaw", "xdg_name": "openclaw"},
    "kilo": {"dot_dir": ".kilo-code", "app_name": "Kilo Code", "xdg_name": "kilo-code"},
    "kiro": {"dot_dir": ".kiro", "app_name": "Kiro", "xdg_name": "kiro"},
    "pi": {"dot_dir": ".pi", "app_name": "Pi", "xdg_name": "pi"},
    "qoder": {"dot_dir": ".qoder", "app_name": "Qoder", "xdg_name": "qoder"},
    "qwen": {"dot_dir": ".qwen", "app_name": "Qwen Code", "xdg_name": "qwen-code"},
    "trae": {"dot_dir": ".trae", "app_name": "Trae", "xdg_name": "trae"},
}

AGENT_ALIASES: dict[str, str] = {
    "claude-code": "claude",
    "claudecode": "claude",
    "open-code": "opencode",
    "antigravity-cli": "antigravity",
    "antigravity-code": "antigravity",
    "kimi-code": "kimi",
    "kimi-code-cli": "kimi",
    "kimi-cli": "kimi",
    "gemini-cli": "gemini",
    "github-copilot-cli": "github-copilot",
    "copilot": "github-copilot",
    "hermes-agent": "hermes",
    "open-claw": "openclaw",
    "openclaw-cli": "openclaw",
    "kilo-code": "kilo",
    "kiro-cli": "kiro",
    "pi-cli": "pi",
    "qwen-code": "qwen",
    "qoder-cli": "qoder",
    "trae-cli": "trae",
}

# Secret patterns to scan for
REGEX_PATTERNS: dict[str, dict[str, Any]] = {
    "openai-api-key": {
        "name": "OpenAI API key",
        "severity": "critical",
        "pattern": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    },
    "anthropic-api-key": {
        "name": "Anthropic API key",
        "severity": "critical",
        "pattern": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    },
    "github-token": {
        "name": "GitHub token",
        "severity": "critical",
        "pattern": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    },
    "aws-access-key": {
        "name": "AWS access key ID",
        "severity": "high",
        "pattern": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    },
    "google-api-key": {
        "name": "Google API key",
        "severity": "high",
        "pattern": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    },
    "slack-token": {
        "name": "Slack token",
        "severity": "high",
        "pattern": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    },
    "stripe-live-key": {
        "name": "Stripe live key",
        "severity": "critical",
        "pattern": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
    },
    "jwt": {
        "name": "JSON Web Token",
        "severity": "high",
        "pattern": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    },
    "database-url": {
        "name": "Database URL",
        "severity": "critical",
        "pattern": re.compile(
            r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s\"'<>`]+"
        ),
    },
    "private-key": {
        "name": "Private key block",
        "severity": "critical",
        "pattern": re.compile(
            r"(?s)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
    },
    "env-secret": {
        "name": "Secret-like env assignment",
        "severity": "medium",
        "pattern": re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|client[_-]?secret)\b\s*[:=]\s*[\"']?([^\s\"',`]{8,})"
        ),
    },
}

SAFE_STRINGS = {
    "sk-spark-secure-key-2026",
    "sk-spark-secure-key",
    "your-api-key",
    "your_key_here",
    "sk-proj-YOUR_API_KEY",
}

BACKUP_DIR = Path(".md/scratch/backups")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class MaskaraScanner:
    """Deep module hiding secret regex matching, file scanning, redaction, and reporting.

    Provides a clean 4-method interface:
    - `scan_text(content, ...)`
    - `redact_text(content, ...)`
    - `perform_scan(targets, ...)`
    - `redact_findings(scan_result)`
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize MaskaraScanner with project root."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.resolve()
        self.project_root = project_root

    def normalize_agent_name(self, name: str) -> str:
        """Normalize agent name to canonical key."""
        clean = name.lower().strip().replace("_", "-").replace(" ", "-")
        return AGENT_ALIASES.get(clean, clean)

    def get_default_roots(self, dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
        """Retrieve system-specific default log paths."""
        home = Path.home()
        roots = [home / dot_dir]
        if sys.platform == "win32":
            for env_var in ["APPDATA", "LOCALAPPDATA"]:
                if val := os.getenv(env_var):
                    roots.append(Path(val) / app_name)
        elif sys.platform == "darwin":
            roots.append(home / "Library" / "Application Support" / app_name)
        else:
            roots.append(home / ".config" / xdg_name)
            roots.append(home / ".local" / "share" / xdg_name)
        return list(dict.fromkeys(roots))

    def resolve_targets(
        self, agent_name: str, custom_root: str | None = None
    ) -> list[dict[str, Any]]:
        """Resolve which target directories/agents to scan."""
        norm = self.normalize_agent_name(agent_name)
        if custom_root:
            return [
                {"agent": norm if norm != "auto" else "custom", "root": Path(custom_root).resolve()}
            ]

        home = Path.home()
        agents_list = list(AGENT_SPECS.keys())

        if norm == "auto":
            existing = []
            for agent in agents_list:
                spec = AGENT_SPECS[agent]
                for path in self.get_default_roots(
                    spec["dot_dir"], spec["app_name"], spec["xdg_name"]
                ):
                    if path.is_dir():
                        existing.append({"agent": agent, "root": path.resolve()})
            return (
                existing
                if existing
                else [{"agent": "claude", "root": (home / ".claude" / "projects").resolve()}]
            )

        if norm == "all":
            all_targets = []
            for agent in agents_list:
                spec = AGENT_SPECS[agent]
                for path in self.get_default_roots(
                    spec["dot_dir"], spec["app_name"], spec["xdg_name"]
                ):
                    all_targets.append({"agent": agent, "root": path.resolve()})
            return all_targets

        if norm not in AGENT_SPECS:
            raise ValueError(f"Unsupported agent: {agent_name}")

        spec = AGENT_SPECS[norm]
        return [
            {"agent": norm, "root": path.resolve()}
            for path in self.get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
        ]

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

    def apply_raw_redactions(
        self, original: bytes, findings: list[dict[str, Any]]
    ) -> tuple[bytes, int]:
        """Substitute secrets index ranges with redaction strings."""
        rewritten = bytearray(original)
        findings_sorted = sorted(findings, key=lambda x: x["start"], reverse=True)
        last_start = len(original) + 1
        replaced = 0

        for f in findings_sorted:
            start, end = f["start"], f["end"]
            if start < 0 or end > len(original) or start >= end:
                continue
            if end > last_start:
                continue

            replacement = f["redaction"].encode("utf-8")
            rewritten[start:end] = replacement
            last_start = start
            replaced += 1

        return bytes(rewritten), replaced

    def backup_and_write(self, path: Path, original: bytes, rewritten: bytes) -> str:
        """Save backup to centralized gitignored directory and write redacted file."""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        abs_path_str = str(path.resolve())
        hash_id = hashlib.sha256(abs_path_str.encode("utf-8")).hexdigest()[:12]
        backup_filename = f"{path.name}.{hash_id}.bak"
        backup_path = BACKUP_DIR / backup_filename

        registry_file = BACKUP_DIR / "registry.json"
        registry = {}
        if registry_file.exists():
            try:
                registry = json.loads(registry_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

        registry[backup_filename] = abs_path_str
        registry_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")

        backup_path.write_bytes(original)
        temp_path = path.with_name(f"{path.name}.maskara-temp")
        temp_path.write_bytes(rewritten)
        if sys.platform == "win32" and path.exists():
            path.unlink()
        temp_path.rename(path)

        return str(backup_path)

    def redact_findings(self, scan_result: dict[str, Any]) -> dict[str, Any]:
        """Execute redaction on findings."""
        grouped: dict[str, list[dict[str, Any]]] = {}
        for f in scan_result["findings"]:
            grouped.setdefault(f["file"], []).append(f)

        files_summary = []
        total_replaced = 0
        total_skipped = 0

        for file_str, findings in grouped.items():
            path = Path(file_str)
            if not path.exists() or path.is_symlink():
                total_skipped += 1
                continue

            try:
                original = path.read_bytes()
                rewritten, replaced = self.apply_raw_redactions(original, findings)

                if replaced == 0 or original == rewritten:
                    total_skipped += 1
                    continue

                backup_path = self.backup_and_write(path, original, rewritten)
                total_replaced += replaced
                files_summary.append(
                    {"path": str(path), "backup_path": backup_path, "replaced": replaced}
                )
            except OSError as e:
                print(f"[Error] Failed to redact {path}: {e}", file=sys.stderr)
                total_skipped += 1

        files_summary.sort(key=lambda x: x["path"])
        return {"files": files_summary, "replaced": total_replaced, "skipped": total_skipped}

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
        """CLI entry point for maskara.py."""
        parser = argparse.ArgumentParser(description="CCBA Maskara offline scanner and redactor")
        parser.add_argument(
            "-v", "--version", action="store_true", help="Print version information"
        )
        subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

        scan_parser = subparsers.add_parser("scan", help="Scan folders for secrets")
        scan_parser.add_argument(
            "-a", "--agent", default="auto", help="Target agent name (or all, auto)"
        )
        scan_parser.add_argument("-r", "--root", help="Explicit root folder path to scan")
        scan_parser.add_argument(
            "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
        )

        report_parser = subparsers.add_parser(
            "report", help="Scan and write Markdown or JSON report"
        )
        report_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
        report_parser.add_argument("-r", "--root", help="Explicit root path to scan")
        report_parser.add_argument(
            "--json", action="store_true", help="Format output report as JSON"
        )
        report_parser.add_argument(
            "-o", "--output", help="Output file path (default: current directory)"
        )
        report_parser.add_argument(
            "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
        )

        redact_parser = subparsers.add_parser(
            "redact", help="Scan and redact secrets (replace with masked tokens)"
        )
        redact_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
        redact_parser.add_argument("-r", "--root", help="Explicit root path to scan and redact")
        redact_parser.add_argument(
            "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
        )

        guard_parser = subparsers.add_parser(
            "guardrails", help="Install safety guardrails and hooks"
        )
        guard_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
        guard_parser.add_argument(
            "--dry-run", action="store_true", help="Log planned actions without writing"
        )

        args = parser.parse_args(args_list)

        if args.version:
            print("Maskara v1.0.0 (Python Edition)")
            return 0

        cmd = args.subcommand
        if not cmd:
            print("[Maskara] Running default full workflow: scan, redact, and report...")
            try:
                targets = self.resolve_targets("auto")
                scan_result = self.perform_scan(targets)
                redact_sum = self.redact_findings(scan_result)
                report_md = self.generate_markdown(scan_result, redact_sum)

                report_path = Path("maskara-report.md")
                report_path.write_text(report_md, encoding="utf-8")
                print(
                    f"[Maskara] Redaction complete ({redact_sum['replaced']} replaced). Report written to {report_path}"
                )
                return (
                    1
                    if any(f["severity"] in ("critical", "high") for f in scan_result["findings"])
                    else 0
                )
            except Exception as e:
                print(f"[Error] Runtime error: {e}", file=sys.stderr)
                return 2

        try:
            if cmd == "scan":
                targets = self.resolve_targets(args.agent, args.root)
                result = self.perform_scan(targets, args.llm)

                if not result["findings"]:
                    print("[Maskara] No sensitive values detected.")
                    return 0

                print(f"[Maskara] Found {len(result['findings'])} sensitive value(s):")
                for f in result["findings"]:
                    print(
                        f"  - {f['file']}:{f['line']} | {f['rule_name']} ({f['severity']}) | Preview: {f['preview']}"
                    )
                return (
                    1
                    if any(f["severity"] in ("critical", "high") for f in result["findings"])
                    else 0
                )

            elif cmd == "redact":
                targets = self.resolve_targets(args.agent, args.root)
                result = self.perform_scan(targets, args.llm)
                redact_sum = self.redact_findings(result)
                print(f"[Maskara] Redaction complete: {redact_sum['replaced']} secret(s) redacted.")
                if redact_sum["files"]:
                    print("Backups created:")
                    for f in redact_sum["files"]:
                        print(f"  - {f['path']} -> {f['backup_path']}")
                return (
                    1
                    if any(f["severity"] in ("critical", "high") for f in result["findings"])
                    else 0
                )

            elif cmd == "report":
                targets = self.resolve_targets(args.agent, args.root)
                result = self.perform_scan(targets, args.llm)
                empty_redact = {"files": [], "replaced": 0, "skipped": 0}

                if args.json:
                    doc = {"result": result, "redaction": empty_redact}
                    report_str = json.dumps(doc, indent=2)
                else:
                    report_str = self.generate_markdown(result, empty_redact)

                out_path = (
                    Path(args.output)
                    if args.output
                    else Path("maskara-report.json" if args.json else "maskara-report.md")
                )
                if out_path.is_dir():
                    out_path = out_path / (
                        "maskara-report.json" if args.json else "maskara-report.md"
                    )

                out_path.write_text(report_str, encoding="utf-8")
                print(f"[Maskara] Report written to {out_path}")
                return 1 if len(result["findings"]) > 0 else 0

            elif cmd == "guardrails":
                changes = self.install_guardrails(args.agent, args.dry_run)
                state = "Dry-run planned" if args.dry_run else "Installed"
                print(f"[Maskara] {state} guardrails changes:")
                for c in changes:
                    print(
                        f"  - [{c['action'].upper()}] {c['path']} (Backup: {c['backup_path'] or 'none'})"
                    )
                return 0

        except Exception as e:
            print(f"[Error] Runtime error: {e}", file=sys.stderr)
            return 2


# ---------------------------------------------------------------------------
# Standalone functions delegating to default MaskaraScanner instance
# ---------------------------------------------------------------------------

_default_scanner = MaskaraScanner()


def normalize_agent_name(name: str) -> str:
    """Normalize agent name (standalone alias)."""
    return _default_scanner.normalize_agent_name(name)


def get_default_roots(dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
    """Retrieve default log roots (standalone alias)."""
    return _default_scanner.get_default_roots(dot_dir, app_name, xdg_name)


def resolve_targets(agent_name: str, custom_root: str | None = None) -> list[dict[str, Any]]:
    """Resolve target directories (standalone alias)."""
    return _default_scanner.resolve_targets(agent_name, custom_root)


def looks_like_session_text(path: Path) -> bool:
    """Check session text extension (standalone alias)."""
    return _default_scanner.looks_like_session_text(path)


def is_binary(filepath: Path) -> bool:
    """Check binary file (standalone alias)."""
    return _default_scanner.is_binary(filepath)


def line_and_column(content: str, offset: int) -> tuple[int, int]:
    """Calculate line and column numbers (standalone alias)."""
    return _default_scanner.line_and_column(content, offset)


def mask_value(val: str) -> str:
    """Mask value (standalone alias)."""
    return _default_scanner.mask_value(val)


def extract_context(content: str, start_offset: int, end_offset: int) -> str:
    """Extract context lines (standalone alias)."""
    return _default_scanner.extract_context(content, start_offset, end_offset)


def detect_secrets_in_text(
    content: str, filepath: str = "", agent: str = "", use_llm: bool = False
) -> list[dict[str, Any]]:
    """Scan string content for secrets (standalone alias)."""
    return _default_scanner.scan_text(content, filepath, agent, use_llm)


def redact_secrets_in_text(content: str, agent: str = "text") -> str:
    """Redact secrets in text string (standalone alias)."""
    return _default_scanner.redact_text(content, agent)


def perform_scan(targets: list[dict[str, Any]], use_llm: bool = False) -> dict[str, Any]:
    """Perform scan across targets (standalone alias)."""
    return _default_scanner.perform_scan(targets, use_llm)


def redact_findings(scan_result: dict[str, Any]) -> dict[str, Any]:
    """Redact findings (standalone alias)."""
    return _default_scanner.redact_findings(scan_result)


def generate_markdown(result: dict[str, Any], redact_summary: dict[str, Any]) -> str:
    """Generate Markdown report (standalone alias)."""
    return _default_scanner.generate_markdown(result, redact_summary)


def install_guardrails(agent_name: str, dry_run: bool = False) -> list[dict[str, str]]:
    """Install guardrails (standalone alias)."""
    return _default_scanner.install_guardrails(agent_name, dry_run)


def main() -> None:
    """CLI entry point (standalone alias)."""
    scanner = MaskaraScanner()
    exit_code = scanner.run_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
