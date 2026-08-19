"""CLI Interface for CCBA Legislative Consolidator."""

import argparse
import sys
from pathlib import Path

from .patcher import LegislativeConsolidator


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Legislative Consolidator — Automated OKF v2.0 Legal Document Patching & VBHN Engine."
    )
    parser.add_argument(
        "--manifest",
        "-m",
        required=True,
        help="Path to patch_manifest.yaml",
    )
    parser.add_argument(
        "--base",
        "-b",
        required=True,
        help="Path to base legal document Markdown file (*.md)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output directory for generated OKF v2.0 artifacts",
    )
    parser.add_argument(
        "--amending",
        "-a",
        default=None,
        help="Optional path to amending document Markdown file (*.md) for content extraction",
    )

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    base_path = Path(args.base)
    output_dir = Path(args.output)
    amending_path = Path(args.amending) if args.amending else None

    print("=================================================================")
    print("        CCBA LEGISLATIVE CONSOLIDATOR (OKF v2.0)                 ")
    print("=================================================================")
    print(f"📄 Manifest: {manifest_path}")
    print(f"📄 Base Document: {base_path}")
    print(f"📁 Output Directory: {output_dir}")
    if amending_path:
        print(f"📄 Amending Document: {amending_path}")
    print("-----------------------------------------------------------------")

    consolidator = LegislativeConsolidator.from_manifest_file(manifest_path)
    result = consolidator.consolidate(
        base_md_path=base_path,
        output_dir=output_dir,
        amending_md_path=amending_path,
    )

    if result.success:
        print("✅ CONSOLIDATION COMPLETED SUCCESSFULLY!")
        print(f"  • Consolidated Markdown: {result.consolidated_md_path}")
        print(f"  • Rich AST clauses.json: {result.clauses_json_path} ({result.total_clauses} clauses)")
        print(f"  • Diff Matrix: {result.diff_matrix_path}")
        print(f"  • Statistics: +{result.added_clauses} added, ~{result.modified_clauses} modified, -{result.repealed_clauses} repealed")
        print("=================================================================")
        sys.exit(0)
    else:
        print("❌ CONSOLIDATION FAILED WITH ERRORS:")
        for err in result.errors:
            print(f"  - {err}")
        print("=================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
