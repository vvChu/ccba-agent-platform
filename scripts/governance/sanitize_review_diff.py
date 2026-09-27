#!/usr/bin/env python3
"""sanitize_review_diff.py - Governance utility to sanitize and audit review diffs.

Scans git diffs or file inputs for credentials and API keys via `ccba-maskara`,
redacting secrets before submission to AI reviewers and enforcing pre-merge checks.

Public CLI / Entrypoint:
    python scripts/governance/sanitize_review_diff.py --base origin/main --head HEAD --check
    python scripts/governance/sanitize_review_diff.py input.patch -o output.patch

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Ensure packages/ccba-maskara/src is importable if not installed in editable mode
_PACKAGE_SRC = Path(__file__).resolve().parent.parent.parent / "packages" / "ccba-maskara" / "src"
if _PACKAGE_SRC.exists() and str(_PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_SRC))

from ccba_maskara import detect_secrets_in_text, redact_secrets_in_text


def fetch_git_diff(base: str, head: str = "HEAD") -> str:
    """Fetch git diff output between base and head references using git CLI.

    Args:
        base: Git base reference (e.g. 'origin/main').
        head: Git head reference (default: 'HEAD').

    Returns:
        Unified diff string output.

    Raises:
        subprocess.CalledProcessError: If git diff command fails.
    """
    cmd = ["git", "diff", f"{base}...{head}"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return proc.stdout


def sanitize_diff(diff_text: str) -> tuple[str, list[dict[str, Any]]]:
    """Scan and redact sensitive tokens in diff text.

    Args:
        diff_text: Raw diff text string.

    Returns:
        Tuple of (sanitized_diff_text, list_of_findings).
    """
    if not diff_text.strip():
        return diff_text, []

    findings = detect_secrets_in_text(diff_text, filepath="diff")
    if not findings:
        return diff_text, []

    sanitized = redact_secrets_in_text(diff_text)
    return sanitized, findings


def generate_report(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate structured audit report summary from detected findings.

    Args:
        findings: List of secret finding dictionaries.

    Returns:
        Dictionary with audit summary and findings list.
    """
    rule_counts: dict[str, int] = {}
    for f in findings:
        rule_id = str(f.get("rule_id", "unknown"))
        rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1

    findings_summary = [
        {
            "rule_id": f.get("rule_id"),
            "rule_name": f.get("rule_name"),
            "severity": f.get("severity"),
            "line": f.get("line"),
            "column": f.get("column"),
            "preview": f.get("preview"),
            "sha256": f.get("sha256"),
        }
        for f in findings
    ]

    return {
        "secrets_detected": len(findings) > 0,
        "total_findings": len(findings),
        "rule_counts": rule_counts,
        "findings": findings_summary,
    }


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the diff sanitizer."""
    parser = argparse.ArgumentParser(
        description="CCBA Maskara Diff Sanitizer & Pre-merge Audit Gate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to input diff file (or '-' for standard input).",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        default=None,
        help="Explicit path to input diff file.",
    )
    parser.add_argument(
        "-b",
        "--base",
        default=None,
        help="Git base reference for comparison (e.g. 'origin/main').",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Git head reference for comparison.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="File path to write sanitized diff (default: stdout if not --check).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Enforce audit gate: exit with code 1 if unredacted secrets are detected.",
    )
    parser.add_argument(
        "--report-json",
        default=None,
        help="Write JSON audit summary report to specified file path.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress informational console output.",
    )
    return parser.parse_args(argv)


def load_input_text(args: argparse.Namespace) -> str:
    """Load diff content according to CLI options (git range, file, or stdin).

    Args:
        args: Parsed arguments namespace.

    Returns:
        Raw input string.
    """
    if args.base:
        return fetch_git_diff(args.base, args.head)

    target_file = args.input_file or args.file
    if target_file and target_file != "-":
        return Path(target_file).read_text(encoding="utf-8", errors="replace")

    # Read from standard input
    if not sys.stdin.isatty() or target_file == "-":
        return sys.stdin.read()

    return ""


def main(argv: Sequence[str] | None = None) -> int:
    """CLI Entrypoint for the Diff Sanitizer and Audit Gate.

    Args:
        argv: Optional command-line arguments sequence.

    Returns:
        Exit code: 0 on success/clean, 1 if secrets detected under --check.
    """
    args = parse_arguments(argv)

    try:
        raw_diff = load_input_text(args)
    except Exception as exc:
        sys.stderr.write(f"[ERROR] Failed to load diff input: {exc}\n")
        return 2

    sanitized_diff, findings = sanitize_diff(raw_diff)
    report = generate_report(findings)

    if args.report_json:
        try:
            report_path = Path(args.report_json)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"[WARN] Failed to write report JSON: {exc}\n")

    if args.output:
        try:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(sanitized_diff, encoding="utf-8")
            if not args.quiet:
                sys.stderr.write(f"[INFO] Sanitized diff written to: {args.output}\n")
        except OSError as exc:
            sys.stderr.write(f"[ERROR] Failed to write output file: {exc}\n")
            return 2
    elif not args.check:
        sys.stdout.write(sanitized_diff)

    if args.check:
        if findings:
            sys.stderr.write(
                f"[SECURITY VIOLATION] Found {len(findings)} secret(s) in review diff:\n"
            )
            for f in findings:
                sys.stderr.write(
                    f"  - Line {f.get('line')}, Col {f.get('column')}: "
                    f"[{f.get('rule_id')}] {f.get('preview')}\n"
                )
            return 1
        if not args.quiet:
            sys.stderr.write("[PASS] No secrets detected in review diff.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
