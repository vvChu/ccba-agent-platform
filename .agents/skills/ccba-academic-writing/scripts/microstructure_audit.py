#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-academic-writing microstructure_audit.

Delegates execution to Layer 1 Deep Seam: mdconverter.audit_microstructure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mdconverter import audit_microstructure


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit academic writing draft paper for stylistic compliance."
    )
    parser.add_argument("file_path", type=Path, help="Path to markdown manuscript file")
    args = parser.parse_args()

    try:
        report = audit_microstructure(args.file_path)
        print(f"[OK] Microstructure Audit Score: {report.overall_readability_score}/100")
        print(f"     Total Paragraphs: {report.total_paragraphs}")
        print(f"     Sections: {', '.join(report.sections_found)}")
        print(f"     CARS Moves: {', '.join(report.cars_moves_found)}")
        print(f"     Findings: {len(report.findings)} issues detected")
        for f in report.findings[:5]:
            print(f"     - [{f.category}] {f.message}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
