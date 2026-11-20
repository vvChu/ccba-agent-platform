"""Pure-stdlib LF-normalized SHA-256 manifest writer and verifier for Tier-0 guardrails.

Shared Tier-0 seam used by ``scripts/spoke/sync`` and
``scripts/_guardrails/check_spoke_cleanliness.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path

MANIFEST_SCHEMA_VERSION = 1
MANIFEST_REL_PATH = "scripts/_guardrails/guardrails_manifest.json"
EXCLUDED_NAMES = frozenset("guardrails_manifest.json module_budget_baseline.json".split())


def compute_lf_sha256(path: Path) -> str:
    """Compute LF-normalized SHA-256 hex digest of a file for cross-OS parity."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _normalize_guardrail_rel(rel: str) -> str | None:
    """Validate and normalize a relative path under scripts/_guardrails/."""
    norm = rel.strip().replace("\\", "/")
    if not norm.startswith("scripts/_guardrails/") or ".." in norm.split("/"):
        return None
    name = norm.rsplit("/", 1)[-1]
    if not name or name in EXCLUDED_NAMES:
        return None
    return norm


def collect_guardrail_hashes(spoke_root: Path, dest_rels: Iterable[str]) -> dict[str, str]:
    """Collect sorted LF-normalized SHA-256 digests for existing scripts/_guardrails/ targets."""
    root = spoke_root.resolve()
    hashes: dict[str, str] = {}
    for raw_rel in sorted({r.strip() for r in dest_rels if r.strip()}):
        norm = _normalize_guardrail_rel(raw_rel)
        if norm is None:
            continue
        target = root / norm
        if target.is_file() and not target.is_symlink():
            hashes[norm] = compute_lf_sha256(target)
    return dict(sorted(hashes.items()))


def write_guardrail_manifest(spoke_root: Path, dest_rels: Iterable[str]) -> Path:
    """Overwrite deterministic guardrails_manifest.json without timestamps or host paths."""
    root = spoke_root.resolve()
    out = root / MANIFEST_REL_PATH
    data = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "files": collect_guardrail_hashes(root, dest_rels),
    }
    body = json.dumps(data, indent=2, sort_keys=True) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(body.encode("utf-8"))
    return out


def verify_guardrail_manifest(spoke_root: Path, manifest_path: Path | None = None) -> list[str]:
    """Verify synced scripts/_guardrails/ files against guardrails_manifest.json fail-closed."""
    root = spoke_root.resolve()
    target = manifest_path if manifest_path is not None else root / MANIFEST_REL_PATH
    try:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"Cannot read guardrail manifest '{MANIFEST_REL_PATH}': {exc}"]
    sv = data.get("schema_version") if isinstance(data, dict) else None
    if type(sv) is not int or sv != MANIFEST_SCHEMA_VERSION:
        return [f"Invalid schema_version in '{MANIFEST_REL_PATH}' (expected 1)."]
    files_map = data.get("files")
    if not isinstance(files_map, dict):
        return [f"Missing or invalid 'files' mapping in '{MANIFEST_REL_PATH}'."]
    violations: list[str] = []
    for rel, expected in sorted(files_map.items()):
        norm = _normalize_guardrail_rel(str(rel))
        if norm is None or not isinstance(expected, str) or len(expected) != 64:
            violations.append(f"Invalid manifest entry '{rel}'.")
            continue
        file_path = root / norm
        if not file_path.is_file() or file_path.is_symlink():
            violations.append(f"{norm}: declared guardrail file is missing.")
            continue
        actual = compute_lf_sha256(file_path)
        if actual != expected.lower():
            violations.append(f"{norm}: SHA-256 mismatch ({expected[:12]} != {actual[:12]}).")
    return violations


def main(argv: list[str] | None = None) -> int:
    """Standalone CLI for verifying Spoke Tier-0 guardrail manifest integrity."""
    parser = argparse.ArgumentParser(description="Verify CCBA Tier-0 guardrail SHA-256 manifest.")
    parser.add_argument("--path", "-p", default=".", help="Target Spoke root directory.")
    parser.add_argument("--verify", action="store_true", help="Verify guardrails_manifest.json.")
    args = parser.parse_args(argv)
    if not args.verify:
        parser.print_help()
        return 1
    root = Path(args.path).resolve()
    manifest_file = root / MANIFEST_REL_PATH
    if not manifest_file.is_file():
        print(f"Missing required manifest '{MANIFEST_REL_PATH}' in {root}.", file=sys.stderr)
        return 1
    violations = verify_guardrail_manifest(root, manifest_file)
    if violations:
        for item in violations:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1
    print(f"[OK] Verified guardrail manifest '{MANIFEST_REL_PATH}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
