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
import ast
import sys
from pathlib import Path

# Hub package import prefixes to monitor
HUB_PACKAGE_PREFIXES = (
    "ccba_legal",
    "ccba_legal_intel",
    "ccba_ai",
    "ccba_harness",
    "ccba_ooxml",
    "ccba_pdf_prep",
    "ccba_qc_core",
    "mdconverter",
    "ccba_notebooklm",
    "ccba_maskara",
)


def scan_file(filepath: Path) -> list[tuple[int, str]]:
    """Scans a Python file for deep Hub package imports using AST parsing.

    Returns list of (line_number, line_content) violations.
    """
    violations: list[tuple[int, str]] = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
    except (UnicodeDecodeError, OSError, SyntaxError):
        return violations

    lines = content.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if not node.module or node.level > 0:
                continue
            parts = node.module.split(".")
            pkg = parts[0]
            if pkg in HUB_PACKAGE_PREFIXES:
                if len(parts) >= 3 or (len(parts) >= 2 and parts[1].startswith("_")):
                    line_num = node.lineno
                    line_content = (
                        lines[line_num - 1].strip()
                        if 0 < line_num <= len(lines)
                        else f"from {node.module} import ..."
                    )
                    violations.append((line_num, line_content))

        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                pkg = parts[0]
                if pkg in HUB_PACKAGE_PREFIXES:
                    if len(parts) >= 3 or (len(parts) >= 2 and parts[1].startswith("_")):
                        line_num = node.lineno
                        line_content = (
                            lines[line_num - 1].strip()
                            if 0 < line_num <= len(lines)
                            else f"import {alias.name}"
                        )
                        violations.append((line_num, line_content))

    # Deduplicate by line number and sort
    return sorted(set(violations), key=lambda x: x[0])


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
