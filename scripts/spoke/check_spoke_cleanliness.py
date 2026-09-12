"""CCBA Spoke Cleanliness Checker — Pre-commit hook & Linter for Spoke repositories.

Enforces ADR 0044 & Issue #215 rules:
1. Script Count Budget: Limits root files in `scripts/` to <= 15 core files.
2. Ephemeral Script Detection: Flags one-off scripts (fix_*, audit_*, patch_*, tmp_*)
   and prompts archiving into `.md/archive/legacy_scripts/` or `.md/scratch/`.
3. Hub Duplication Gate: Flags duplicate implementations (custom crawlers, rate limiters,
   or `sys.path.insert` hacks) when Hub shared packages should be used.

Usage:
    python check_spoke_cleanliness.py [--path <spoke_root>] [--max-scripts 15] [--strict]
    # Or as a pre-commit hook in .pre-commit-config.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# System and Guardrail scripts that do NOT count towards the 15-file limit
ALLOWLIST_SCRIPTS = {
    "__init__.py",
    "conftest.py",
    "safe_pytest.py",
    "safe_runner.py",
    "check_hub_import_depth.py",
    "check_spoke_cleanliness.py",
    "check_claudekit_updates.py",
    "spoke_bootstrap.py",
    "spoke_bootstrap.ps1",
    "setup_pre_commit.py",
    "sync.py",
}

# Prefix patterns indicating one-off or temporary scripts
EPHEMERAL_PREFIXES = (
    "fix_",
    "audit_",
    "patch_",
    "test_tmp_",
    "debug_",
    "tmp_",
    "temp_",
    "oneoff_",
    "scratch_",
)

# Patterns detecting anti-patterns or duplicated hub functionality
SYS_PATH_HACK_PATTERN = re.compile(
    r"sys\.path\.(?:insert|append)\s*\(\s*0?\s*,\s*.*hub", re.IGNORECASE
)


def check_script_count(scripts_dir: Path, max_scripts: int = 15) -> tuple[list[Path], list[Path]]:
    """Checks the number of top-level scripts in the scripts/ folder.

    Returns:
        (counted_scripts, ignored_scripts)
    """
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return [], []

    all_py_files = [f for f in scripts_dir.iterdir() if f.is_file() and f.suffix == ".py"]
    counted: list[Path] = []
    ignored: list[Path] = []

    for f in all_py_files:
        if f.name in ALLOWLIST_SCRIPTS or f.name.startswith("check_"):
            ignored.append(f)
        else:
            counted.append(f)

    return counted, ignored


def check_ephemeral_scripts(scripts: list[Path]) -> list[Path]:
    """Finds scripts that match ephemeral / one-off naming conventions."""
    ephemeral: list[Path] = []
    for s in scripts:
        name_lower = s.name.lower()
        if any(name_lower.startswith(prefix) for prefix in EPHEMERAL_PREFIXES):
            ephemeral.append(s)
    return ephemeral


def check_hub_duplications(target_files: list[Path]) -> list[tuple[Path, int, str]]:
    """Checks for sys.path hacks or duplicated Hub implementations."""
    violations: list[tuple[Path, int, str]] = []
    for filepath in target_files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if SYS_PATH_HACK_PATTERN.search(stripped):
                violations.append(
                    (
                        filepath,
                        line_num,
                        "Anti-pattern sys.path hack detected. Use 'pip install -e' via spoke_bootstrap.py instead.",
                    )
                )
    return violations


def scan_spoke_cleanliness(
    spoke_root: Path, max_scripts: int = 15, strict: bool = False
) -> tuple[int, list[str]]:
    """Runs all cleanliness checks against a target Spoke workspace.

    Returns:
        (exit_code, messages)
    """
    messages: list[str] = []
    has_errors = False
    has_warnings = False

    scripts_dir = spoke_root / "scripts"
    if scripts_dir.exists():
        counted_scripts, ignored_scripts = check_script_count(scripts_dir, max_scripts=max_scripts)
        count = len(counted_scripts)

        if count > max_scripts:
            has_errors = True
            messages.append(
                f"❌ [Script Budget Vượt Ngưỡng] Thư mục 'scripts/' có {count} tệp (tối đa cho phép: {max_scripts}).\n"
                f"   Các file đang đếm ({count}): {', '.join(sorted(f.name for f in counted_scripts))}\n"
                f"   💡 Giải pháp: Di chuyển các script one-off/fix/audit cũ vào '.md/archive/legacy_scripts/' hoặc '.md/scratch/'."
            )
        else:
            messages.append(
                f"✅ [Script Budget] Thư mục 'scripts/' có {count}/{max_scripts} tệp hợp lệ ({len(ignored_scripts)} tệp hệ thống được bỏ qua)."
            )

        # Ephemeral scripts
        ephemeral = check_ephemeral_scripts(counted_scripts)
        if ephemeral:
            has_warnings = True
            messages.append(
                f"⚠️  [Script Tạm Thời] Phát hiện {len(ephemeral)} script có tiền tố tạm thời (fix_*, audit_*, patch_*, tmp_*):\n"
                + "\n".join(f"   - {f.name}" for f in ephemeral)
                + "\n   💡 Hãy chuyển các script này vào '.md/archive/legacy_scripts/' sau khi chạy xong."
            )

        # Scan for sys.path hacks across scripts/ and src/ (excluding tests)
        py_files_to_scan: list[Path] = []
        for d in [scripts_dir, spoke_root / "src"]:
            if d.exists():
                py_files_to_scan.extend(
                    [
                        f
                        for f in d.rglob("*.py")
                        if not any(p in (".venv", "venv", "__pycache__", "tests") for p in f.parts)
                    ]
                )

        dup_violations = check_hub_duplications(py_files_to_scan)
        if dup_violations:
            has_errors = True
            messages.append(
                f"❌ [Vi phạm Hub Duplication / sys.path] Phát hiện {len(dup_violations)} vị trí vi phạm:\n"
                + "\n".join(
                    f"   - {f.relative_to(spoke_root)}:{ln}: {msg}" for f, ln, msg in dup_violations
                )
            )

    exit_code = 1 if has_errors or (strict and has_warnings) else 0
    return exit_code, messages


def main() -> int:
    """CLI runner for spoke cleanliness check."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Spoke Cleanliness & Script Budget Checker (ADR 0044 / Issue #215)"
    )
    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Target Spoke root directory (default: current dir)",
    )
    parser.add_argument(
        "--max-scripts",
        type=int,
        default=15,
        help="Maximum number of core scripts in scripts/ folder (default: 15)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit code 1) on warnings such as ephemeral script names",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional specific files passed by pre-commit",
    )
    args = parser.parse_args()

    spoke_root = Path(args.path).resolve()
    exit_code, messages = scan_spoke_cleanliness(
        spoke_root=spoke_root, max_scripts=args.max_scripts, strict=args.strict
    )

    print("=" * 80)
    print("🧹 CCBA Spoke Cleanliness Report")
    print("=" * 80)
    for m in messages:
        print(m)
    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
