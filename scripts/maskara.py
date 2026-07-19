#!/usr/bin/env python3
"""CCBA Maskara - Offline security scanner and redactor for coding-agent logs.

This tool helps detect and redact sensitive values (such as API keys, tokens,
private keys) in agent logs and files. It runs completely offline by default
with an optional AI Gateway context check to reduce false positives.
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

BACKUP_DIR = Path(".md/scratch/backups")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def normalize_agent_name(name: str) -> str:
    """Normalize agent name to canonical key.

    Args:
        name: Raw agent name or alias.

    Returns:
        Canonical agent name.
    """
    clean = name.lower().strip().replace("_", "-").replace(" ", "-")
    return AGENT_ALIASES.get(clean, clean)


def get_default_roots(dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
    """Retrieve system-specific default configuration/log paths.

    Args:
        dot_dir: Dot directory path (e.g. .claude/projects).
        app_name: Name of application (Windows path component).
        xdg_name: Linux/XDG config name.

    Returns:
        List of Path objects for potential folders.
    """
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

    return list(dict.fromkeys(roots))  # Deduplicate


def resolve_targets(agent_name: str, custom_root: str | None = None) -> list[dict[str, Any]]:
    """Resolve which target directories/agents to scan.

    Args:
        agent_name: Canonical or alias name, or 'all', 'auto'.
        custom_root: Explicit path to scan.

    Returns:
        List of dict targets containing 'agent' and 'root' keys.
    """
    norm = normalize_agent_name(agent_name)
    if custom_root:
        return [
            {"agent": norm if norm != "auto" else "custom", "root": Path(custom_root).resolve()}
        ]

    home = Path.home()
    agents_list = list(AGENT_SPECS.keys())

    if norm == "auto":
        # Scan only folder that actually exist on machine
        existing = []
        for agent in agents_list:
            spec = AGENT_SPECS[agent]
            for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"]):
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
            for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"]):
                all_targets.append({"agent": agent, "root": path.resolve()})
        return all_targets

    if norm not in AGENT_SPECS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    spec = AGENT_SPECS[norm]
    return [
        {"agent": norm, "root": path.resolve()}
        for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
    ]


def looks_like_session_text(path: Path) -> bool:
    """Determine if filename pattern looks like session/logs text.

    Args:
        path: File Path to inspect.

    Returns:
        True if text files likely contain session details.
    """
    name = path.name.lower()
    ext = path.suffix.lower()

    if ext in [".json", ".jsonl", ".md", ".txt", ".log", ".yaml", ".yml", ".toml", ".env", ".xml"]:
        return True
    if name.startswith(".env"):
        return True

    keywords = ["session", "conversation", "transcript", "history"]
    return any(kw in name for kw in keywords)


def is_binary(filepath: Path) -> bool:
    """Check if file is binary by searching for null bytes in initial sample.

    Args:
        filepath: Path to file.

    Returns:
        True if file content contains binary markers.
    """
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except OSError:
        return True


def line_and_column(content: str, offset: int) -> tuple[int, int]:
    """Calculate 1-indexed line and column numbers for character offset.

    Args:
        content: String content of file.
        offset: Offset of match.

    Returns:
        Tuple of (line, column).
    """
    lines = content[:offset].split("\n")
    return len(lines), len(lines[-1]) + 1


def mask_value(val: str) -> str:
    """Mask sensitive string value leaving only terminal characters.

    Args:
        val: Raw secret.

    Returns:
        Masked secret string.
    """
    clean = val.replace("\r", "").replace("\n", "\\n")
    if len(clean) <= 8:
        return "***"
    return f"{clean[:4]}...{clean[-4:]}"


def ask_llm_gateway(finding: dict[str, Any], context: str) -> bool:
    """Query AI Gateway to verify if finding is a true secret or false positive.

    Args:
        finding: Target finding details.
        context: 3 lines before & after context.

    Returns:
        True if confirmed as positive, False if LLM labels it sample/safe.
    """
    try:
        from ccba_ai import ai
    except ImportError:
        # If ccba_ai is not installed, fail-securely by assuming it is true secret
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
        print(f"[Warning] AI Gateway validation failed, defaulting to True: {e}", file=sys.stderr)
        return True


def extract_context(content: str, start_offset: int, end_offset: int) -> str:
    """Extract context lines surrounding a finding.

    Args:
        content: Content string.
        start_offset: Start offset.
        end_offset: End offset.

    Returns:
        String of 3 lines before and after.
    """
    before = content[:start_offset].split("\n")[-3:]
    after = content[end_offset:].split("\n")[:3]
    middle = content[start_offset:end_offset]
    return "\n".join(before + [middle] + after)


SAFE_STRINGS = {
    "sk-spark-secure-key-2026",
    "sk-spark-secure-key",
    "your-api-key",
    "your_key_here",
    "sk-proj-YOUR_API_KEY",
}


def detect_secrets_in_text(
    content: str, filepath: str, agent: str, use_llm: bool = False
) -> list[dict[str, Any]]:
    """Scan string content with regular expressions.

    Args:
        content: Target string contents.
        filepath: Source filepath.
        agent: Labeling agent name.
        use_llm: Set True to trigger AI Gateway validations.

    Returns:
        List of finding dicts.
    """
    findings: list[dict[str, Any]] = []

    for rule_id, rule_spec in REGEX_PATTERNS.items():
        pattern = rule_spec["pattern"]
        for match in pattern.finditer(content):
            # If env-secret, we only capture group 1 (value) to redact
            if rule_id == "env-secret":
                val = match.group(1)
                start, end = match.start(1), match.end(1)
            else:
                val = match.group(0)
                start, end = match.start(), match.end()

            if val in SAFE_STRINGS:
                continue

            if "MASKARA_REDACTED" in val:
                continue

            line, col = line_and_column(content, start)
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
                "preview": mask_value(val),
                "sha256": hashlib.sha256(val.encode("utf-8")).hexdigest(),
                "redaction": f"[MASKARA_REDACTED:{rule_id}]",
            }

            if use_llm:
                context_str = extract_context(content, start, end)
                if not ask_llm_gateway(finding, context_str):
                    continue

            findings.append(finding)

    # Resolve overlapping findings (keep first match or largest)
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


def scan_file(
    agent: str, path: Path, use_llm: bool = False
) -> tuple[list[dict[str, Any]], int, int]:
    """Perform scanning process on a single file.

    Args:
        agent: Name of the agent.
        path: Path object of file.
        use_llm: Use LLM for validation.

    Returns:
        Tuple of (findings_list, scanned_count, skipped_count).
    """
    try:
        if path.is_symlink() or path.is_dir():
            return [], 0, 1
        if path.stat().st_size > MAX_FILE_SIZE or not looks_like_session_text(path):
            return [], 0, 1
        if is_binary(path):
            return [], 0, 1

        content = path.read_text(encoding="utf-8", errors="ignore")
        findings = detect_secrets_in_text(content, str(path), agent, use_llm)
        return findings, 1, 0
    except OSError:
        return [], 0, 1


def perform_scan(targets: list[dict[str, Any]], use_llm: bool = False) -> dict[str, Any]:
    """Perform scanning across resolved targets.

    Args:
        targets: Resolved agent roots.
        use_llm: Validate with LLM.

    Returns:
        Result summary dict.
    """
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
            f, sc, sk = scan_file(agent, root, use_llm)
            findings.extend(f)
            scanned_count += sc
            skipped_count += sk
            continue

        for root_dir, dirs, files in os.walk(root):
            # Prune directory search path
            dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs]
            for file in files:
                filepath = Path(root_dir) / file
                f, sc, sk = scan_file(agent, filepath, use_llm)
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


def is_json_valid(data: bytes) -> bool:
    """Validate JSON bytes.

    Args:
        data: Byte buffer.

    Returns:
        True if valid JSON.
    """
    try:
        json.loads(data.decode("utf-8"))
        return True
    except (ValueError, TypeError):
        return False


def is_jsonl_valid(data: bytes) -> bool:
    """Validate JSONL bytes line by line.

    Args:
        data: Byte buffer.

    Returns:
        True if valid JSONL.
    """
    lines = data.split(b"\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            json.loads(stripped.decode("utf-8"))
        except (ValueError, TypeError):
            return False
    return True


def count_lines(data: bytes) -> int:
    """Count number of lines in byte buffer.

    Args:
        data: Byte buffer.

    Returns:
        Number of lines.
    """
    if not data:
        return 0
    return data.count(b"\n") + 1


def validate_structured(filepath: Path, before: bytes, after: bytes) -> bool:
    """Verify that redaction doesn't break structured file syntax.

    Args:
        filepath: Path to file.
        before: Original bytes.
        after: Redacted bytes.

    Returns:
        True if valid or not structured file.
    """
    ext = filepath.suffix.lower()
    if ext == ".json":
        if is_json_valid(before.strip()) and not is_json_valid(after.strip()):
            return False
    elif ext == ".jsonl":
        if is_jsonl_valid(before) and not is_jsonl_valid(after):
            return False
        if count_lines(before) != count_lines(after):
            return False
    return True


def redact_json_val(value: Any) -> tuple[Any, int]:
    """Recursively search and redact string values in JSON objects.

    Args:
        value: Any json value.

    Returns:
        Tuple of (redacted_value, replaced_count).
    """
    if isinstance(value, str):
        findings = detect_secrets_in_text(value, "", "")
        if not findings:
            return value, 0
        # In-place redact
        raw_val = value.encode("utf-8")
        raw_val, replaced = apply_raw_redactions(raw_val, findings)
        return raw_val.decode("utf-8"), replaced
    elif isinstance(value, list):
        replaced = 0
        new_list = []
        for val in value:
            nv, rep = redact_json_val(val)
            new_list.append(nv)
            replaced += rep
        return new_list, replaced
    elif isinstance(value, dict):
        replaced = 0
        new_dict = {}
        for k, val in value.items():
            nv, rep = redact_json_val(val)
            new_dict[k] = nv
            replaced += rep
        return new_dict, replaced
    return value, 0


def redact_structured(filepath: Path, original: bytes) -> tuple[bytes, int]:
    """Fallback parser for JSON/JSONL.

    Args:
        filepath: Target filepath.
        original: Original bytes.

    Returns:
        Tuple of (new_bytes, replaced_count).
    """
    ext = filepath.suffix.lower()
    if ext == ".json":
        try:
            data = json.loads(original.decode("utf-8"))
            redacted_data, replaced = redact_json_val(data)
            out = json.dumps(redacted_data, indent=2).encode("utf-8")
            if original.endswith(b"\n"):
                out += b"\n"
            return out, replaced
        except (ValueError, TypeError):
            return original, 0

    if ext == ".jsonl":
        lines = original.split(b"\n")
        rewritten = []
        replaced = 0
        for line in lines:
            if not line.strip():
                rewritten.append(line)
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                redacted_data, rep = redact_json_val(data)
                rewritten.append(json.dumps(redacted_data).encode("utf-8"))
                replaced += rep
            except (ValueError, TypeError):
                rewritten.append(line)
        return b"\n".join(rewritten), replaced

    return original, 0


def apply_raw_redactions(original: bytes, findings: list[dict[str, Any]]) -> tuple[bytes, int]:
    """Substitute secrets index ranges with redaction strings.

    Args:
        original: Original file bytes.
        findings: File specific findings list.

    Returns:
        Tuple of (redacted_bytes, replaced_count).
    """
    rewritten = bytearray(original)
    # Apply from end of file to beginning to keep offset indices intact
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


def backup_and_write(path: Path, original: bytes, rewritten: bytes) -> str:
    """Save backup to centralized gitignored directory and write rewritten file.

    Args:
        path: Target file path.
        original: Original content.
        rewritten: Redacted content.

    Returns:
        Backup file path.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique backup name using path hash
    abs_path_str = str(path.resolve())
    hash_id = hashlib.sha256(abs_path_str.encode("utf-8")).hexdigest()[:12]
    backup_filename = f"{path.name}.{hash_id}.bak"
    backup_path = BACKUP_DIR / backup_filename

    # Save backup registry details
    registry_file = BACKUP_DIR / "registry.json"
    registry = {}
    if registry_file.exists():
        try:
            registry = json.loads(registry_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    registry[backup_filename] = abs_path_str
    registry_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    # Write backup and replace file atomically
    backup_path.write_bytes(original)

    # Atomic replace
    temp_path = path.with_name(f"{path.name}.maskara-temp")
    temp_path.write_bytes(rewritten)
    if sys.platform == "win32" and path.exists():
        path.unlink()
    temp_path.rename(path)

    return str(backup_path)


def redact_findings(scan_result: dict[str, Any]) -> dict[str, Any]:
    """Execute redaction on findings.

    Args:
        scan_result: Scanned result output.

    Returns:
        Summary dict of redactions.
    """
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
            rewritten, replaced = apply_raw_redactions(original, findings)

            if replaced == 0 or original == rewritten:
                total_skipped += 1
                continue

            if not validate_structured(path, original, rewritten):
                # Fallback to structured parsing
                rewritten, replaced = redact_structured(path, original)
                if replaced == 0 or original == rewritten:
                    total_skipped += 1
                    continue

            backup_path = backup_and_write(path, original, rewritten)
            total_replaced += replaced
            files_summary.append(
                {"path": str(path), "backup_path": backup_path, "replaced": replaced}
            )
        except OSError as e:
            print(f"[Error] Failed to redact {path}: {e}", file=sys.stderr)
            total_skipped += 1

    files_summary.sort(key=lambda x: x["path"])
    return {"files": files_summary, "replaced": total_replaced, "skipped": total_skipped}


def generate_markdown(result: dict[str, Any], redact_summary: dict[str, Any]) -> str:
    """Generate Markdown report contents.

    Args:
        result: Scan results.
        redact_summary: Redaction summary.

    Returns:
        Markdown string.
    """
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

    # Summarize by rules
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


def get_guardrail_content() -> str:
    """Retrieve guardrail instructions template.

    Returns:
        Guardrail instructions string.
    """
    return """# Maskara Privacy Guardrails

Never print, quote, summarize, or store raw secrets from `.env` files, shell
history, cloud CLIs, keychains, password managers, session logs, or agent logs.

When a task needs to verify a credential exists, access it by variable name and
report only presence, prefix class, provider, or a masked preview. Prefer
commands that avoid echoing values. Do not paste full API keys, private keys,
database URLs, bearer tokens, cookies, or session tokens into conversation text.

Before sharing logs, reports, repro bundles, or terminal output, run
`maskara scan` or `maskara report` and redact findings. If a secret may have
been exposed to an agent or remote provider, tell the user to rotate it.

If a tool blocks access to a sensitive file, ask the user for explicit approval
instead of trying alternate commands to bypass the block.
"""


def get_skill_content() -> str:
    """Retrieve privacy skill template.

    Returns:
        Privacy skill string.
    """
    return """---
name: maskara-privacy
description: Prevent accidental disclosure of secrets in coding-agent sessions and route cleanup through maskara.
---

# Maskara Privacy Skill

Use this skill whenever a task touches secrets, credentials, `.env` files,
agent session logs, shell history, or generated reports that may contain private
values.

Rules:
- Do not print raw secrets.
- Use masked previews only.
- Prefer checking variable names or key presence over reading values.
- Run `maskara scan` before sharing agent logs.
- Run `maskara report` when the user needs rotation guidance.
- Run `maskara` only when the user wants scan, redaction, and report together.
- If redaction finds credentials, advise rotation. Local redaction does not
  revoke secrets already shared with providers.
"""


def get_hook_content() -> str:
    """Retrieve PowerShell privacy hook script.

    Returns:
        PowerShell script content.
    """
    return """$payload = if ($args.Count -gt 0) { $args -join " " } else { [Console]::In.ReadToEnd() }
$lower = $payload.ToLowerInvariant()

$blocked = @(
  ".env",
  "printenv",
  "authorization:",
  "bearer ",
  "private key",
  "secret"
)

foreach ($term in $blocked) {
  if ($lower.Contains($term)) {
    Write-Error "maskara guardrails: command may expose secrets. Use masked checks or run maskara report."
    exit 2
  }
}

exit 0
"""


def install_guardrails(agent_name: str, dry_run: bool = False) -> list[dict[str, str]]:
    """Install guardrail instructions and hooks for target agent.

    Args:
        agent_name: Target agent name, or 'all', 'auto'.
        dry_run: Only log actions without writing files.

    Returns:
        List of dict representing changes made.
    """
    changes: list[dict[str, str]] = []

    # Resolve target agents
    norm = normalize_agent_name(agent_name)
    if norm in ["auto", "all"]:
        target_agents = []
        for candidate in AGENT_SPECS:
            spec = AGENT_SPECS[candidate]
            for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"]):
                if path.is_dir():
                    target_agents.append(candidate)
                    break
        if not target_agents:
            target_agents = ["claude", "codex"]
    else:
        if norm not in AGENT_SPECS:
            raise ValueError(f"Unsupported guardrails agent: {agent_name}")
        target_agents = [norm]

    for agent in target_agents:
        spec = AGENT_SPECS[agent]
        roots = get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
        if not roots:
            continue
        primary_root = roots[0]

        # Decide file paths based on agent type
        if agent == "claude":
            plans = [
                {
                    "path": primary_root / "CLAUDE.md",
                    "action": "append",
                    "content": get_guardrail_content(),
                },
                {
                    "path": primary_root / "skills" / "maskara-privacy" / "SKILL.md",
                    "action": "write",
                    "content": get_skill_content(),
                },
                {
                    "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                    "action": "write",
                    "content": get_hook_content(),
                },
            ]
        elif agent == "codex":
            plans = [
                {
                    "path": primary_root / "AGENTS.md",
                    "action": "append",
                    "content": get_guardrail_content(),
                },
                {
                    "path": primary_root / "skills" / "maskara-privacy" / "SKILL.md",
                    "action": "write",
                    "content": get_skill_content(),
                },
                {
                    "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                    "action": "write",
                    "content": get_hook_content(),
                },
            ]
        else:
            plans = [
                {
                    "path": primary_root / "maskara-guardrails.md",
                    "action": "append",
                    "content": get_guardrail_content(),
                },
                {
                    "path": primary_root / "hooks" / "maskara-privacy-hook.ps1",
                    "action": "write",
                    "content": get_hook_content(),
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
                        # Backup first
                        bp = path.with_suffix(f"{path.suffix}.maskara.bak")
                        shutil.copy2(path, bp)
                        backup_path = str(bp)

                        # Append
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


def main() -> None:
    """Parse CLI arguments and run selected subcommand workflow."""
    parser = argparse.ArgumentParser(description="CCBA Maskara offline scanner and redactor")
    parser.add_argument("-v", "--version", action="store_true", help="Print version information")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: scan
    scan_parser = subparsers.add_parser("scan", help="Scan folders for secrets")
    scan_parser.add_argument(
        "-a", "--agent", default="auto", help="Target agent name (or all, auto)"
    )
    scan_parser.add_argument("-r", "--root", help="Explicit root folder path to scan")
    scan_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    # Subcommand: report
    report_parser = subparsers.add_parser("report", help="Scan and write Markdown or JSON report")
    report_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    report_parser.add_argument("-r", "--root", help="Explicit root path to scan")
    report_parser.add_argument("--json", action="store_true", help="Format output report as JSON")
    report_parser.add_argument(
        "-o", "--output", help="Output file path (default: current directory)"
    )
    report_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    # Subcommand: redact
    redact_parser = subparsers.add_parser(
        "redact", help="Scan and redact secrets (replace with masked tokens)"
    )
    redact_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    redact_parser.add_argument("-r", "--root", help="Explicit root path to scan and redact")
    redact_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    # Subcommand: guardrails
    guard_parser = subparsers.add_parser("guardrails", help="Install safety guardrails and hooks")
    guard_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    guard_parser.add_argument(
        "--dry-run", action="store_true", help="Log planned actions without writing"
    )

    # Parse args
    args = parser.parse_args()

    if args.version:
        print("Maskara v1.0.0 (Python Edition)")
        sys.exit(0)

    cmd = args.subcommand
    if not cmd:
        # Default full workflow: scan -> redact -> report
        print("[Maskara] Running default full workflow: scan, redact, and report...")
        try:
            targets = resolve_targets("auto")
            scan_result = perform_scan(targets)
            redact_sum = redact_findings(scan_result)
            report_md = generate_markdown(scan_result, redact_sum)

            report_path = Path("maskara-report.md")
            report_path.write_text(report_md, encoding="utf-8")
            print(
                f"[Maskara] Redaction complete ({redact_sum['replaced']} replaced). Report written to {report_path}"
            )

            sys.exit(1 if any(f["severity"] in ("critical", "high") for f in scan_result["findings"]) else 0)
        except Exception as e:
            print(f"[Error] Runtime error: {e}", file=sys.stderr)
            sys.exit(2)

    try:
        if cmd == "scan":
            targets = resolve_targets(args.agent, args.root)
            result = perform_scan(targets, args.llm)

            if not result["findings"]:
                print("[Maskara] No sensitive values detected.")
                sys.exit(0)

            print(f"[Maskara] Found {len(result['findings'])} sensitive value(s):")
            for f in result["findings"]:
                print(
                    f"  - {f['file']}:{f['line']} | {f['rule_name']} ({f['severity']}) | Preview: {f['preview']}"
                )
            sys.exit(1 if any(f["severity"] in ("critical", "high") for f in result["findings"]) else 0)

        elif cmd == "redact":
            targets = resolve_targets(args.agent, args.root)
            result = perform_scan(targets, args.llm)
            redact_sum = redact_findings(result)
            print(f"[Maskara] Redaction complete: {redact_sum['replaced']} secret(s) redacted.")
            if redact_sum["files"]:
                print("Backups created:")
                for f in redact_sum["files"]:
                    print(f"  - {f['path']} -> {f['backup_path']}")
            sys.exit(1 if any(f["severity"] in ("critical", "high") for f in result["findings"]) else 0)

        elif cmd == "report":
            targets = resolve_targets(args.agent, args.root)
            result = perform_scan(targets, args.llm)

            # Since report subcommand doesn't redact, we pass empty redaction summary
            empty_redact = {"files": [], "replaced": 0, "skipped": 0}

            if args.json:
                doc = {"result": result, "redaction": empty_redact}
                report_str = json.dumps(doc, indent=2)
            else:
                report_str = generate_markdown(result, empty_redact)

            out_path = (
                Path(args.output)
                if args.output
                else Path("maskara-report.json" if args.json else "maskara-report.md")
            )
            if out_path.is_dir():
                out_path = out_path / ("maskara-report.json" if args.json else "maskara-report.md")

            out_path.write_text(report_str, encoding="utf-8")
            print(f"[Maskara] Report written to {out_path}")
            sys.exit(1 if len(result["findings"]) > 0 else 0)

        elif cmd == "guardrails":
            changes = install_guardrails(args.agent, args.dry_run)
            state = "Dry-run planned" if args.dry_run else "Installed"
            print(f"[Maskara] {state} guardrails changes:")
            for c in changes:
                print(
                    f"  - [{c['action'].upper()}] {c['path']} (Backup: {c['backup_path'] or 'none'})"
                )
            sys.exit(0)

    except Exception as e:
        print(f"[Error] Runtime error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
