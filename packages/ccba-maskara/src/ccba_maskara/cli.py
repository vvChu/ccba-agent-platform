"""Command Line Interface for Maskara."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._scanner import MaskaraScanner


def run_cli(args_list: list[str] | None = None, scanner: MaskaraScanner | None = None) -> int:
    """Execute Maskara CLI commands."""
    if scanner is None:
        from ._scanner import MaskaraScanner

        scanner = MaskaraScanner()

    parser = argparse.ArgumentParser(description="CCBA Maskara offline scanner and redactor")
    parser.add_argument("-v", "--version", action="store_true", help="Print version information")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    scan_parser = subparsers.add_parser("scan", help="Scan folders for secrets")
    scan_parser.add_argument(
        "-a", "--agent", default="auto", help="Target agent name (or all, auto)"
    )
    scan_parser.add_argument("-r", "--root", help="Explicit root folder path to scan")
    scan_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    report_parser = subparsers.add_parser("report", help="Scan and write Markdown or JSON report")
    report_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    report_parser.add_argument("-r", "--root", help="Explicit root path to scan")
    report_parser.add_argument("--json", action="store_true", help="Format output report as JSON")
    report_parser.add_argument(
        "-o", "--output", help="Output file path (default: current directory)"
    )
    report_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    redact_parser = subparsers.add_parser(
        "redact", help="Scan and redact secrets (replace with masked tokens)"
    )
    redact_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    redact_parser.add_argument("-r", "--root", help="Explicit root path to scan and redact")
    redact_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    guard_parser = subparsers.add_parser("guardrails", help="Install safety guardrails and hooks")
    guard_parser.add_argument("-a", "--agent", default="auto", help="Target agent name")
    guard_parser.add_argument(
        "--dry-run", action="store_true", help="Log planned actions without writing"
    )

    hist_parser = subparsers.add_parser(
        "scan-history", help="Scan Git history across commits for leaked secrets"
    )
    hist_parser.add_argument(
        "--all-branches", action="store_true", default=True, help="Scan all branches"
    )
    hist_parser.add_argument(
        "-n", "--max-count", type=int, default=None, help="Limit number of commits to scan"
    )

    args = parser.parse_args(args_list)

    if args.version:
        print("Maskara v1.0.0 (Python Edition)")
        return 0

    cmd = args.subcommand
    if not cmd:
        print("[Maskara] Running default full workflow: scan, redact, and report...")
        try:
            targets = scanner.resolve_targets("auto")
            scan_result = scanner.perform_scan(targets)
            redact_sum = scanner.redact_findings(scan_result)
            report_md = scanner.generate_markdown(scan_result, redact_sum)

            report_path = Path("maskara-report.md")
            report_path.write_text(report_md, encoding="utf-8")
            print(
                f"[Maskara] Redaction complete ({redact_sum['replaced']} replaced). Report written to {report_path}"
            )
            return (
                1
                if any(f["severity"] in ("critical", "high") for f in scan_result["findings"])
                else 0
            )
        except Exception as e:
            print(f"[Error] Runtime error: {e}", file=sys.stderr)
            return 2

    try:
        if cmd == "scan":
            targets = scanner.resolve_targets(args.agent, args.root)
            result = scanner.perform_scan(targets, args.llm)

            if not result["findings"]:
                print("[Maskara] No sensitive values detected.")
                return 0

            print(f"[Maskara] Found {len(result['findings'])} sensitive value(s):")
            for f in result["findings"]:
                print(
                    f"  - {f['file']}:{f['line']} | {f['rule_name']} ({f['severity']}) | Preview: {f['preview']}"
                )
            return (
                1 if any(f["severity"] in ("critical", "high") for f in result["findings"]) else 0
            )

        elif cmd == "redact":
            targets = scanner.resolve_targets(args.agent, args.root)
            result = scanner.perform_scan(targets, args.llm)
            redact_sum = scanner.redact_findings(result)
            print(f"[Maskara] Redaction complete: {redact_sum['replaced']} secret(s) redacted.")
            if redact_sum["files"]:
                print("Backups created:")
                for f in redact_sum["files"]:
                    print(f"  - {f['path']} -> {f['backup_path']}")
            return (
                1 if any(f["severity"] in ("critical", "high") for f in result["findings"]) else 0
            )

        elif cmd == "report":
            targets = scanner.resolve_targets(args.agent, args.root)
            result = scanner.perform_scan(targets, args.llm)
            empty_redact = {"files": [], "replaced": 0, "skipped": 0}

            if args.json:
                doc = {"result": result, "redaction": empty_redact}
                report_str = json.dumps(doc, indent=2)
            else:
                report_str = scanner.generate_markdown(result, empty_redact)

            out_path = (
                Path(args.output)
                if args.output
                else Path("maskara-report.json" if args.json else "maskara-report.md")
            )
            if out_path.is_dir():
                out_path = out_path / ("maskara-report.json" if args.json else "maskara-report.md")

            out_path.write_text(report_str, encoding="utf-8")
            print(f"[Maskara] Report written to {out_path}")
            return 1 if len(result["findings"]) > 0 else 0

        elif cmd == "guardrails":
            changes = scanner.install_guardrails(args.agent, args.dry_run)
            state = "Dry-run planned" if args.dry_run else "Installed"
            print(f"[Maskara] {state} guardrails changes:")
            for c in changes:
                print(
                    f"  - [{c['action'].upper()}] {c['path']} (Backup: {c['backup_path'] or 'none'})"
                )
            return 0

        elif cmd == "scan-history":
            import subprocess

            cmd_args = ["git", "log", "-p", "-U0", "--full-history"]
            if args.all_branches:
                cmd_args.append("--all")
            if args.max_count:
                cmd_args.extend(["-n", str(args.max_count)])

            print("[Maskara] Scanning Git history diffs...")
            proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
            )

            current_commit = ""
            current_file = ""
            history_findings = []

            if proc.stdout:
                for line in proc.stdout:
                    if line.startswith("commit "):
                        current_commit = line.strip().split()[1]
                    elif line.startswith("diff --git "):
                        parts = line.strip().split()
                        current_file = parts[-1].lstrip("b/") if len(parts) >= 4 else ""
                    elif line.startswith("+") and not line.startswith("+++"):
                        if any(
                            t in current_file
                            for t in ("/tests/", "test_", "/test_cases/", "_rules.py", "maskara.py")
                        ):
                            continue
                        added = line[1:].strip()
                        findings = scanner.scan_text(added)
                        for f in findings:
                            if f["severity"] in ("critical", "high"):
                                history_findings.append(
                                    {
                                        "commit": current_commit,
                                        "file": current_file,
                                        "rule_name": f["rule_name"],
                                        "severity": f["severity"],
                                        "preview": f["preview"],
                                    }
                                )

            proc.wait()

            if not history_findings:
                print("[Maskara] Git history is 100% clean. No secrets found.")
                return 0

            print(
                f"[Maskara] Found {len(history_findings)} sensitive value(s) in non-test Git history:"
            )
            for hf in history_findings[:20]:
                print(
                    f"  - Commit {hf['commit'][:8]} | {hf['file']} | {hf['rule_name']} ({hf['severity']}) | {hf['preview']}"
                )
            if len(history_findings) > 20:
                print(f"  ... and {len(history_findings) - 20} more.")
            return 1

    except Exception as e:
        print(f"[Error] Runtime error: {e}", file=sys.stderr)
        return 2

    return 0


def main() -> None:
    """CLI entry point for maskara."""
    exit_code = run_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
