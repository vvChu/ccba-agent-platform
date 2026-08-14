"""Byte-level redaction, backup management, and file rewriting logic for Maskara."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BACKUP_DIR = Path(".md/scratch/backups")


def apply_raw_redactions(original: bytes, findings: list[dict[str, Any]]) -> tuple[bytes, int]:
    """Substitute secrets index ranges with redaction strings in bytearray."""
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


def backup_and_write(
    path: Path, original: bytes, rewritten: bytes, backup_dir: Path = BACKUP_DIR
) -> str:
    """Save backup to centralized gitignored directory and write redacted file."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    abs_path_str = str(path.resolve())
    hash_id = hashlib.sha256(abs_path_str.encode("utf-8")).hexdigest()[:12]
    backup_filename = f"{path.name}.{hash_id}.bak"
    backup_path = backup_dir / backup_filename

    registry_file = backup_dir / "registry.json"
    registry: dict[str, str] = {}
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


def redact_findings(scan_result: dict[str, Any], backup_dir: Path = BACKUP_DIR) -> dict[str, Any]:
    """Execute redaction on findings grouped by file."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for f in scan_result.get("findings", []):
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

            backup_path = backup_and_write(path, original, rewritten, backup_dir)
            total_replaced += replaced
            files_summary.append(
                {"path": str(path), "backup_path": backup_path, "replaced": replaced}
            )
        except OSError as e:
            print(f"[Error] Failed to redact {path}: {e}", file=sys.stderr)
            total_skipped += 1

    files_summary.sort(key=lambda x: x["path"])
    return {"files": files_summary, "replaced": total_replaced, "skipped": total_skipped}
