"""CCBA Legal Knowledge — Visual & Footnote Parity CI Gate (Gate 4).

Audits all Markdown documents in legal_docs/ for:
1. Double bullets (- -  or * * ).
2. Trapped table footnotes inside table cells (| _1) ... |).
3. Concatenated inline dashes inside notes (: - ...; - ...).
4. Raw unformatted table superscripts (REI 60 1) instead of <sup>1)</sup>).
5. Consecutive/redundant _CHÚ THÍCH:_ headers.
6. Unbulleted technical classification codes (LT, BC, SK, ĐT, K0..3).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class VisualParityAuditor:
    """Audits markdown document bundles for visual formatting anomalies and broken layouts."""

    def __init__(self, legal_docs_root: Path | str = Path("legal_docs")) -> None:
        self.legal_docs_root = Path(legal_docs_root)

    def audit(self) -> dict[str, Any]:
        """Perform visual and footnote parity audit across all Markdown files."""
        all_md_files = (
            sorted(self.legal_docs_root.rglob("*.md")) if self.legal_docs_root.exists() else []
        )
        critical_issues: list[str] = []
        warning_issues: list[str] = []

        for md_path in all_md_files:
            if md_path.name in (
                "index.md",
                "dead_ends.md",
                "log.md",
                "README.md",
            ):
                continue

            rel_path = (
                str(md_path.relative_to(self.legal_docs_root))
                if self.legal_docs_root in md_path.parents
                else md_path.name
            )
            content = md_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # 1. Check double bullets
            for idx, line in enumerate(lines, 1):
                if re.match(r"^\s*[-*]\s+[-*]\s+", line):
                    critical_issues.append(f"[{rel_path}:L{idx}] DOUBLE_BULLET: {line.strip()}")

            # 2. Check consecutive _CHÚ THÍCH:_ headers
            for idx, line in enumerate(lines, 1):
                if line.strip() == "_CHÚ THÍCH:_" and idx < len(lines):
                    next_lines = [
                        lines[j].strip()
                        for j in range(idx, min(len(lines), idx + 3))
                        if lines[j].strip()
                    ]
                    if len(next_lines) > 0 and next_lines[0] == "_CHÚ THÍCH:_":
                        critical_issues.append(
                            f"[{rel_path}:L{idx}] DUPLICATE_NOTE_HEADER: Consecutive _CHÚ THÍCH:_"
                        )

            # 3. Check trapped table footnotes in table rows
            for idx, line in enumerate(lines, 1):
                if line.startswith("|") and re.search(
                    r"\|\s*(_[1-9]\)|_CHÚ THÍCH|_GHI CHÚ|_Đối với)", line
                ):
                    critical_issues.append(
                        f"[{rel_path}:L{idx}] TRAPPED_TABLE_FOOTNOTE: {line.strip()[:70]}..."
                    )

            # 4. Check concatenated inline dashes inside notes
            for idx, line in enumerate(lines, 1):
                stripped = line.strip()
                if re.search(
                    r"(?:như sau|điều kiện sau|sau đây|bao gồm):\s*-\s+.*?[;.]\s*-\s+",
                    stripped,
                    re.IGNORECASE,
                ):
                    critical_issues.append(
                        f"[{rel_path}:L{idx}] CONCATENATED_INLINE_DASHES: {stripped[:80]}..."
                    )

            # 5. Check for unformatted in-table superscripts (e.g. REI 60 1) )
            for idx, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("|") and stripped.endswith("|"):
                    raw_sup = re.findall(
                        r"\b([A-Z]{1,4}\s*\d+|\d+)\s+([1-9]\))(?!\<|/sup)",
                        stripped,
                    )
                    if raw_sup:
                        critical_issues.append(
                            f"[{rel_path}:L{idx}] RAW_TABLE_SUPERSCRIPT: {raw_sup} in {stripped[:60]}..."
                        )

            # 6. Check for unbulleted standard classification codes
            for idx, line in enumerate(lines, 1):
                st = line.strip()
                if re.match(
                    r"^(LT[1-4]|BC[1-3]|SK[1-3]|ĐT[1-4]|Ch[1-4]|K[0-3])\s+\(",
                    st,
                ):
                    critical_issues.append(
                        f"[{rel_path}:L{idx}] UNBULLETED_CLASSIFICATION: {st[:50]}"
                    )

        passed = len(critical_issues) == 0
        return {
            "passed": passed,
            "total_files": len(all_md_files),
            "critical_errors_count": len(critical_issues),
            "warning_count": len(warning_issues),
            "critical_errors": critical_issues,
            "warnings": warning_issues,
        }


def audit_visual_parity(legal_docs_root: Path | str = Path("legal_docs")) -> int:
    """CLI runner helper for visual parity audit."""
    auditor = VisualParityAuditor(legal_docs_root=legal_docs_root)
    result = auditor.audit()

    print("=================================================================")
    print("   CCBA VISUAL & FOOTNOTE PARITY AUDIT GATE (GATE 4)             ")
    print("=================================================================")
    print(f"Total Markdown Files Audited: {result['total_files']}")
    print(f"Critical Formatting Errors  : {result['critical_errors_count']}")
    print(f"Format Warnings             : {result['warning_count']}")
    print("-----------------------------------------------------------------")

    if not result["passed"]:
        print("❌ FAILED: The following visual parity errors must be resolved:\n")
        for err in result["critical_errors"][:25]:
            print(f"  -> {err}")
        if result["critical_errors_count"] > 25:
            print(f"  ... and {result['critical_errors_count'] - 25} more errors.")
        return 1

    print("✅ PASSED: 100% Visual Parity, Clean Lists & Footnotes Verified!")
    print("=================================================================\n")
    return 0
