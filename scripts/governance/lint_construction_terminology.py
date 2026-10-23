#!/usr/bin/env python3
"""lint_construction_terminology.py - Master CI Terminology Linter Gate (COND-18, ADR-0059).

Enforces canonical statutory, technical, and governance terminology across
proposals, documentation, and consulting artifacts. Flags prohibited synonyms
while strictly respecting immutable citations, verbatim legal quotes, and code blocks.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Add project root to sys.path for cross-package imports
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ccba_legal.lexicon.loader import load_canonical_taxonomy
from ccba_legal.lexicon.masker import ImmutableSpanMasker
from ccba_legal.lexicon.normalizer import CanonicalTermNormalizer


@dataclass(frozen=True)
class TerminologyViolation:
    """Represents a forbidden terminology violation."""

    file_path: str
    line: int
    column: int
    forbidden_term: str
    canonical_term: str
    canonical_id: str
    line_snippet: str


def is_exempt_line(raw_line: str) -> bool:
    """Checks if a line contains an explicit exemption comment or documents forbidden terms."""
    low = raw_line.lower()
    exempt_markers = (
        "ccba:allow-term",
        "ccba-lexicon:allow",
        "vi_forbidden",
        "thuật ngữ cấm",
        "dịch sai",
        "prohibited synonym",
        "cấm dùng",
    )
    return any(marker in low for marker in exempt_markers)


def collect_target_files(target_path: Path) -> list[Path]:
    """Collects candidate files for terminology inspection."""
    if target_path.is_file():
        return [target_path]

    collected: list[Path] = []
    ignored_parts = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "site-packages",
    }

    for p in target_path.rglob("*.md"):
        if any(part in p.parts for part in ignored_parts):
            continue
        collected.append(p)

    return sorted(collected, key=lambda x: x.as_posix())


def scan_file_content(
    file_path: Path,
    normalizer: CanonicalTermNormalizer,
    masker: ImmutableSpanMasker,
) -> list[TerminologyViolation]:
    """Scans a single file for forbidden construction terminology with table awareness."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    # Step 1: Mask citations, quotes, brands, and code
    masked_content, _ = masker.mask(content)
    violations: list[TerminologyViolation] = []

    lines = masked_content.splitlines()
    raw_lines = content.splitlines()

    in_forbidden_table = False

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        raw_line = raw_lines[line_idx] if line_idx < len(raw_lines) else line
        trimmed = raw_line.strip()

        # Track markdown table boundaries
        if trimmed.startswith("|") and trimmed.endswith("|"):
            if is_exempt_line(trimmed):
                in_forbidden_table = True
            if in_forbidden_table:
                continue
        else:
            in_forbidden_table = False

        # Skip exempted documentation lines
        if is_exempt_line(raw_line):
            continue

        for pattern, canonical_vi, canonical_id, _ in normalizer._compiled_forbidden_rules:
            for match in pattern.finditer(line):
                violations.append(
                    TerminologyViolation(
                        file_path=file_path.as_posix(),
                        line=line_num,
                        column=match.start() + 1,
                        forbidden_term=match.group(0),
                        canonical_term=canonical_vi,
                        canonical_id=canonical_id,
                        line_snippet=raw_line.strip()[:100],
                    )
                )

    return violations


def run_terminology_linter(
    target_path: Path,
    check_mode: bool = True,
    fix_mode: bool = False,
) -> tuple[int, list[TerminologyViolation]]:
    """Runs terminology linter over target path and optionally applies fixes."""
    files = collect_target_files(target_path)
    taxonomy = load_canonical_taxonomy()
    masker = ImmutableSpanMasker()
    normalizer = CanonicalTermNormalizer(taxonomy=taxonomy, masker=masker)

    all_violations: list[TerminologyViolation] = []

    for file_path in files:
        if fix_mode:
            raw_text = file_path.read_text(encoding="utf-8")
            report = normalizer.normalize(raw_text)
            if report.has_changes:
                file_path.write_text(report.normalized_text, encoding="utf-8")

        violations = scan_file_content(file_path, normalizer, masker)
        all_violations.extend(violations)

    exit_code = 1 if (check_mode and len(all_violations) > 0) else 0
    return exit_code, all_violations


def main() -> None:
    """CLI entry point for construction terminology linter."""
    parser = argparse.ArgumentParser(description="CCBA Canonical Terminology Linter")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(".agents/proposals"),
        help="Target file or directory to scan (default: .agents/proposals)",
    )
    parser.add_argument("--check", action="store_true", default=True, help="Exit 1 on violations")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations in place")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    target = args.path.resolve() if args.path.is_absolute() else _ROOT / args.path

    exit_code, violations = run_terminology_linter(
        target_path=target,
        check_mode=args.check,
        fix_mode=args.fix,
    )

    if args.json:
        data = [asdict(v) for v in violations]
        print(
            json.dumps(
                {"total_violations": len(violations), "violations": data},
                indent=2,
                ensure_ascii=False,
            )
        )
        sys.exit(exit_code)

    if violations:
        print(
            f"❌ [CCILF Terminology Linter] Found {len(violations)} violation(s):", file=sys.stderr
        )
        for v in violations:
            print(
                f"  {v.file_path}:{v.line}:{v.column} -> '{v.forbidden_term}' "
                f"is prohibited. Use '{v.canonical_term}' [{v.canonical_id}].\n"
                f"    Snippet: {v.line_snippet}",
                file=sys.stderr,
            )
        sys.exit(exit_code)

    print(
        f"✅ [CCILF Terminology Linter] All inspected files in '{args.path}' comply with canonical terminology."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
