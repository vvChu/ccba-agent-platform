"""CCBA Hub Import Depth Checker — Pre-commit hook for Spoke repositories.

Enforces ADR 0044 rule: Spoke code must only import from top-level Hub packages
(depth ≤ 2). Deep imports (depth ≥ 3) bypass the __all__ API contract and are
forbidden.

Examples:
    ✅ from ccba_legal import ChromeCDP
    ✅ from ccba_ai import ai
    ❌ from ccba_legal.crawler.chrome_cdp import _internal_helper
    ❌ from ccba_harness.core.locks import ProcessLock

Usage:
    python check_hub_import_depth.py [--path <spoke_root>]
    # Or as pre-commit hook in .pre-commit-config.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Hub package import prefixes to monitor
HUB_PACKAGE_PREFIXES = (
    "ccba_legal",
    "ccba_ai",
    "ccba_harness",
    "ccba_ooxml",
    "ccba_pdf_prep",
    "mdconverter",
    "ccba_notebooklm",
    "ccba_maskara",
)

# Pattern: from ccba_xxx.submodule.deep_module import X  (depth >= 3)
# Matches: from ccba_legal.crawler.chrome_cdp import ...
# Matches: import ccba_legal.crawler.chrome_cdp
DEEP_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+"
    r"(" + "|".join(re.escape(p) for p in HUB_PACKAGE_PREFIXES) + r")"
    r"\.\w+\.\w+"  # at least 2 dots = depth >= 3
)


def scan_file(filepath: Path) -> list[tuple[int, str]]:
    """Scans a Python file for deep Hub package imports.

    Returns list of (line_number, line_content) violations.
    """
    violations: list[tuple[int, str]] = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations

    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue
        if DEEP_IMPORT_PATTERN.match(stripped):
            violations.append((line_num, stripped))

    return violations


def main() -> int:
    """Scans Spoke Python files for deep Hub package imports."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Hub Import Depth Checker (ADR 0044)")
    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Root directory to scan (default: current dir)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to check (for pre-commit integration)",
    )
    args = parser.parse_args()

    # Collect files to scan
    target_files: list[Path] = []
    if args.files:
        target_files = [Path(f) for f in args.files if f.endswith(".py")]
    else:
        root = Path(args.path).resolve()
        # Scan root .py files + scripts/, src/, tests/
        target_files.extend(root.glob("*.py"))
        for scan_dir in [root / "scripts", root / "src", root / "tests"]:
            if scan_dir.exists():
                target_files.extend(scan_dir.rglob("*.py"))

    # Exclude .venv, __pycache__, .git, .agents, .md
    target_files = [
        f
        for f in target_files
        if not any(
            part in (".venv", "venv", "__pycache__", ".git", "node_modules", ".agents", ".md")
            for part in f.parts
        )
    ]

    total_violations = 0
    for filepath in sorted(set(target_files)):
        violations = scan_file(filepath)
        if violations:
            total_violations += len(violations)
            for line_num, line_content in violations:
                print(f"{filepath}:{line_num}: {line_content}")

    if total_violations > 0:
        print(
            f"\n❌ Phát hiện {total_violations} vi phạm Import Depth (ADR 0044).\n"
            "   Quy tắc: Chỉ import từ top-level Hub package.\n"
            "   ✅ Đúng:  from ccba_legal import ChromeCDP\n"
            "   ❌ Sai:   from ccba_legal.crawler.chrome_cdp import ChromeCDP\n"
            "   Nếu cần symbol chưa có trong top-level, tạo issue đề xuất bổ sung __all__.",
        )
        return 1

    if target_files:
        print(f"✅ Đã quét {len(target_files)} file(s), không có vi phạm Import Depth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
