"""CCBA Legal Knowledge — Visual & Footnote Parity CI Gate (Gate 4 & ADR 0029/0030).

Audits all Markdown documents in legal_docs/ for:
1. Double bullets (- -  or * * ).
2. Consecutive/redundant _CHÚ THÍCH:_ headers.
3. Trapped table footnotes inside table cells (| _1) ... |).
4. Concatenated inline dashes inside notes (: - ...; - ...).
5. Raw unformatted table superscripts (REI 60 1) instead of <sup>1)</sup>).
6. Unbulleted technical classification codes (LT, BC, SK, ĐT, K0..3).
7. Redundant bullet before footnote header (- **CHÚ THÍCH:).
8. Raw uncleaned HTML table tags (<table>, <tr>, <td>).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def lint_document(md_path: Path) -> list[str]:
    """Lint a single Markdown file for visual formatting and layout parity issues."""
    errors: list[str] = []
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Cannot read file: {exc}"]

    lines = text.splitlines()
    in_display_math = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 2:
            pass
        elif "$$" in stripped:
            in_display_math = not in_display_math
            continue

        if in_display_math:
            continue


        # 1. Check double bullets
        if re.match(r"^\s*[-*]\s+[-*]\s+", line):
            errors.append(f"Line {idx}: DOUBLE_BULLET: '{stripped}'")

        # 2. Check consecutive _CHÚ THÍCH:_ headers
        if stripped == "_CHÚ THÍCH:_" and idx < len(lines):
            next_lines = [
                lines[j].strip()
                for j in range(idx, min(len(lines), idx + 3))
                if lines[j].strip()
            ]
            if len(next_lines) > 0 and next_lines[0] == "_CHÚ THÍCH:_":
                errors.append(f"Line {idx}: DUPLICATE_NOTE_HEADER: Consecutive _CHÚ THÍCH:_")

        # 3. Check trapped table footnotes in table rows
        if line.startswith("|") and re.search(
            r"\|\s*(_[1-9]\)|_CHÚ THÍCH|_GHI CHÚ|_Đối với)", line
        ):
            errors.append(f"Line {idx}: TRAPPED_TABLE_FOOTNOTE: '{stripped[:70]}...'")

        # 4. Check concatenated inline dashes inside notes
        if re.search(
            r"(?:như sau|điều kiện sau|sau đây|bao gồm):\s*-\s+.*?[;.]\s*-\s+",
            stripped,
            re.IGNORECASE,
        ):
            errors.append(f"Line {idx}: CONCATENATED_INLINE_DASHES: '{stripped[:80]}...'")

        # 5. Check for unformatted in-table superscripts (e.g. REI 60 1) )
        if stripped.startswith("|") and stripped.endswith("|"):
            raw_sup = re.findall(
                r"\b([A-Z]{1,4}\s*\d+|\d+)\s+([1-9]\))(?!<|/sup)",
                stripped,
            )
            if raw_sup:
                errors.append(f"Line {idx}: RAW_TABLE_SUPERSCRIPT: {raw_sup} in '{stripped[:60]}...'")

        # 6. Check for unbulleted standard classification codes
        if re.match(r"^(LT[1-4]|BC[1-3]|SK[1-3]|ĐT[1-4]|Ch[1-4]|K[0-3])\s+\(", stripped):
            errors.append(f"Line {idx}: UNBULLETED_CLASSIFICATION: '{stripped[:50]}'")

        # 7. Check redundant bullet before CHÚ THÍCH / GHI CHÚ header
        if re.match(r"^[-*+]\s+(?:\*\*)?(?:CHÚ THÍCH|GHI CHÚ|Chú thích|Ghi chú)\s*\d*[:\.]?", stripped):
            if re.search(r"^[-*+]\s+(?:\*\*)?CHÚ THÍCH\s+\d+:", stripped):
                errors.append(f"Line {idx}: REDUNDANT_NOTE_BULLET: Redundant bullet before footnote header: '{stripped}'")

        # 8. Check raw HTML table tags
        if re.search(r"<(?:table|thead|tbody|tr|th|td)\b", stripped, re.IGNORECASE):
            errors.append(f"Line {idx}: UNCLEAN_HTML_TABLE: Unclean raw HTML table tag found: '{stripped}'")

        # 9. Check squashed notes with <br> tag (ADR 0030)
        if re.search(r"<br>\s*(?:\*\*)?CHÚ THÍCH", stripped, re.IGNORECASE):
            errors.append(f"Line {idx}: SQUASHED_NOTE_BR: Squashed footnote using <br> tag: '{stripped[:70]}'")

        # 10. Check unclosed or broken markdown table rows (ADR 0030)
        if stripped.startswith("|") and not stripped.endswith("|"):
            errors.append(f"Line {idx}: BROKEN_TABLE_ROW: Table row does not end with '|': '{stripped[:70]}'")
        if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", stripped):
            prev = lines[idx - 2].strip() if idx >= 2 else ""
            if not (prev.startswith("|") and prev.endswith("|")):
                errors.append(f"Line {idx}: INVALID_TABLE_HEADER: Table separator preceded by invalid header: '{prev[:70]}'")


    # 10. Check monotonic footnote numbering sequence (ADR 0030)
    is_amendment = "sua_doi" in md_path.stem.lower() or "sources" in md_path.parts
    if not is_amendment:
        chunks = re.split(r"(?=\n#{1,4}\s+|\n<a id=)", text)
        for chunk in chunks:
            # Match plain, italic (_CHÚ THÍCH:_), bold (**CHÚ THÍCH:**) markers
            labels = [
                re.sub(r"[_*]", "", m.group(1)).strip().upper()
                for m in re.finditer(r"(?:^|[^a-zA-Z0-9])([_*]*(?:CHÚ THÍCH|Chú thích)(?:\s+\d+)?[_*]*):", chunk, re.IGNORECASE)
            ]
            if labels:
                has_note_2 = any("CHÚ THÍCH 2" in lbl for lbl in labels)
                has_note_1 = any("CHÚ THÍCH 1" in lbl for lbl in labels)
                if has_note_2 and not has_note_1:
                    errors.append("MISSING_NOTE_1: Missing 'CHÚ THÍCH 1:' in section where 'CHÚ THÍCH 2:' exists.")


    return errors




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
        audited_files_count = 0

        for md_path in all_md_files:
            if md_path.name in (
                "index.md",
                "dead_ends.md",
                "log.md",
                "README.md",
            ):
                continue
            audited_files_count += 1

            rel_path = (
                str(md_path.relative_to(self.legal_docs_root))
                if self.legal_docs_root in md_path.parents
                else md_path.name
            )

            file_errors = lint_document(md_path)
            for err in file_errors:
                critical_issues.append(f"[{rel_path}] {err}")

        passed = len(critical_issues) == 0
        return {
            "passed": passed,
            "total_files": audited_files_count,
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
