"""CLI entrypoint for CCBA Personal Sandbox Deliverable Promotion (ADR 0046).

Usage:
    python scripts/promote_sandbox.py --target "D:/path/to/target-spoke" --files "output/report.md" --pgv "PGV-2026-08-014"
"""

from __future__ import annotations

import argparse
import sys

from scripts.spoke.sandbox_promoter import SandboxPromoter


def main() -> int:
    """Parse CLI arguments and run sandbox promotion."""
    parser = argparse.ArgumentParser(
        description="Promote deliverable files from personal sandbox to target project spoke."
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        default=".",
        help="Path to personal sandbox workspace root (default: current directory).",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to target project delivery spoke root.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Relative paths of files to promote (e.g. output/report.md scripts/tool.py).",
    )
    parser.add_argument(
        "--pgv",
        type=str,
        default=None,
        help="Optional Phiếu Giao Việc code for IDOP staging (e.g. PGV-2026-08-014).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate promotion without modifying files.",
    )

    args = parser.parse_args()

    try:
        promoter = SandboxPromoter(sandbox_root=args.sandbox)
        result = promoter.promote(
            target_spoke_path=args.target,
            files=args.files,
            pgv_code=args.pgv,
            dry_run=args.dry_run,
        )
        print(f"\n✅ {result.message}")
        if result.staged_receipt_path:
            print(f"📋 IDOP Staged Receipt: {result.staged_receipt_path}")
        return 0
    except Exception as e:
        print(f"\n❌ Error during promotion: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
