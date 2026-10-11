#!/usr/bin/env python3
"""scripts/governance/normalize_peer_telemetry_costs.py - Normalizes historical xAI ticks scaling in telemetry.

ADR-0064 / ADR-0065 Audit remediation:
Fixes historical markdown files in .md/peer_exchange/ where cost_usd was computed by dividing ticks by 10,000.0
instead of 10^10, resulting in costs being inflated by 10^6.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def normalize_cost_value(val: Any) -> float | None:
    """Divides value by 10^6 if it exceeds 1000.0."""
    try:
        f = float(val)
        if f > 1000.0:
            return round(f / 1_000_000.0, 4)
    except (ValueError, TypeError):
        pass
    return None


def process_frontmatter_dict(data: dict[str, Any]) -> bool:
    """Recursively checks and updates cost_usd in YAML dictionary."""
    modified = False

    for k, v in list(data.items()):
        if k == "cost_usd":
            normalized = normalize_cost_value(v)
            if normalized is not None and normalized != v:
                data[k] = normalized
                modified = True
        elif isinstance(v, dict):
            if process_frontmatter_dict(v):
                modified = True
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    if process_frontmatter_dict(item):
                        modified = True

    return modified


def normalize_file(file_path: Path, apply: bool = False) -> bool:
    """Normalizes telemetry cost_usd in a single markdown file."""
    content = file_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not fm_match:
        return False

    raw_yaml = fm_match.group(1)
    body = content[fm_match.end() :]

    try:
        data = yaml.safe_load(raw_yaml)
    except Exception:
        return False

    if not isinstance(data, dict):
        return False

    if not process_frontmatter_dict(data):
        return False

    new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True, width=1000)
    new_content = f"---\n{new_yaml}---\n{body}"

    if apply:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  [APPLIED] Normalized: {file_path.name}")
    else:
        print(f"  [DRY-RUN] Found inflated cost in: {file_path.name}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize legacy inflated peer telemetry costs in .md/peer_exchange/."
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply modifications to disk (default: dry-run)."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(".md/peer_exchange"),
        help="Target directory (default: .md/peer_exchange).",
    )
    args = parser.parse_args()

    target_dir = args.dir.resolve()
    if not target_dir.exists():
        print(f"Directory does not exist: {target_dir}")
        return 1

    print(f"Scanning markdown files in {target_dir} (apply={args.apply})...")
    modified_count = 0
    for md_file in sorted(target_dir.glob("*.md")):
        if normalize_file(md_file, apply=args.apply):
            modified_count += 1

    print(
        f"\nDone. {modified_count} file(s) {'updated' if args.apply else 'identified for update'}."
    )

    if args.apply and modified_count > 0:
        print("Refreshing status.json exchange stats...")
        try:
            from ccba_harness.peer import run_sync_cycle

            run_sync_cycle(target_dir)
            print("[OK] status.json refreshed successfully.")
        except Exception as e:
            print(f"[WARNING] Could not refresh status.json: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
