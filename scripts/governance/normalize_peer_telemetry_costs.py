#!/usr/bin/env python3
"""scripts/governance/normalize_peer_telemetry_costs.py - Normalizes historical peer telemetry and risk_score.

ADR-0064 / ADR-0065 Audit remediation:
1. Fixes historical markdown files in .md/peer_exchange/ where cost_usd was inflated by 10^6.
2. Enforces $0.00 cost for local GPU models (qwen-local*).
3. Reconciles CombinedTelemetry.cost_usd with the sum of profile_breakdown costs.
4. Normalizes legacy 100-point risk_score values (> 5) to the strict 1..5 scale.
"""

from __future__ import annotations

import argparse
import os
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


def _normalize_legacy_risk_score(val: Any) -> int | None:
    """Normalizes legacy integer/float risk_score > 5 into the strict 1..5 range."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    f = float(val)
    if f > 5.0:
        scaled = int(round(f / 10.0)) if f <= 10.0 else int(round(f / 20.0))
        return min(5, max(1, scaled or 1))
    return None


def process_frontmatter_dict(data: dict[str, Any]) -> bool:
    """Recursively checks and updates cost_usd and legacy risk_score in YAML dictionary."""
    modified = False
    model_str = str(data.get("primary_model") or data.get("model") or "").lower()
    is_local_model = "qwen-local" in model_str or "local" in model_str

    for k, v in list(data.items()):
        if k == "risk_score":
            norm_risk = _normalize_legacy_risk_score(v)
            if norm_risk is not None and norm_risk != v:
                data[k] = norm_risk
                modified = True
        elif k == "cost_usd":
            if is_local_model and float(v or 0.0) != 0.0:
                data[k] = 0.0
                modified = True
            else:
                normalized = normalize_cost_value(v)
                if normalized is not None and normalized != v:
                    data[k] = normalized
                    modified = True
        elif isinstance(v, dict):
            if process_frontmatter_dict(v):
                modified = True
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and process_frontmatter_dict(item):
                    modified = True

    breakdown = data.get("profile_breakdown")
    if isinstance(breakdown, dict) and breakdown:
        expected_sum = round(
            sum(float(p.get("cost_usd", 0.0)) for p in breakdown.values() if isinstance(p, dict)),
            4,
        )
        if "cost_usd" in data and float(data["cost_usd"]) != expected_sum:
            data["cost_usd"] = expected_sum
            modified = True

    return modified


def normalize_file(file_path: Path, apply: bool = False) -> bool:
    """Normalizes telemetry cost_usd and legacy risk_score in a single markdown file."""
    content = file_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not fm_match:
        return False

    raw_yaml = fm_match.group(1)
    end_pos = fm_match.end()
    body = content[end_pos:]

    try:
        data = yaml.safe_load(raw_yaml)
    except Exception:
        return False

    if not isinstance(data, dict) or not process_frontmatter_dict(data):
        return False

    new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True, width=1000)
    new_content = f"---\n{new_yaml}---\n{body}"

    if apply:
        orig_stat = file_path.stat()
        file_path.write_text(new_content, encoding="utf-8")
        os.utime(file_path, (orig_stat.st_atime, orig_stat.st_mtime))
        print(f"  [APPLIED] Normalized: {file_path.name}")
    else:
        print(f"  [DRY-RUN] Needs normalization: {file_path.name}")

    return True


def main() -> int:
    """CLI entry point for normalizing historical peer exchange frontmatter."""
    parser = argparse.ArgumentParser(
        description="Normalize legacy peer telemetry costs and risk scores in .md/peer_exchange/."
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
    modified_count = sum(
        1
        for md_file in sorted(target_dir.glob("*.md"))
        if normalize_file(md_file, apply=args.apply)
    )
    print(
        f"\nDone. {modified_count} file(s) {'updated' if args.apply else 'identified for update'}."
    )

    if args.apply:
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
