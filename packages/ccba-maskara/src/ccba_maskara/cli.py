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
        "--staged", action="store_true", help="Scan staged files in current git repository"
    )
    scan_parser.add_argument(
        "--files", nargs="*", default=None, help="Explicit list of files to scan"
    )
    scan_parser.add_argument(
        "--llm", action="store_true", help="Use AI Gateway to double-verify findings"
    )

    hooks_parser = subparsers.add_parser(
        "init-hooks", help="Install tracked pre-commit hook and configure git core.hooksPath"
    )
    hooks_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite hook even if custom core.hooksPath exists",
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
        print("Maskara v1.2.0 (Python Edition)")
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
            if getattr(args, "staged", False):
                import subprocess

                try:
                    res = subprocess.run(
                        ["git", "diff", "--cached", "--name-only", "--diff-filter=d", "-z"],
                        capture_output=True,
                        timeout=10,
                    )
                    if res.returncode != 0:
                        err_msg = res.stderr.decode("utf-8", errors="replace").strip()
                        print(
                            f"[Maskara Error] 'git diff' failed with exit code {res.returncode}. Not inside a Git repository? {err_msg}",
                            file=sys.stderr,
                        )
                        return 2
                    raw_paths = [p for p in res.stdout.split(b"\x00") if p]
                    staged_files = [p.decode("utf-8", errors="replace") for p in raw_paths]
                except FileNotFoundError:
                    print("[Maskara Error] 'git' command not found. Fail-closed.", file=sys.stderr)
                    return 2

                if not staged_files:
                    print("[Maskara] No staged files to scan.")
                    return 0

                findings = []
                for fpath_str in staged_files:
                    p = Path(fpath_str)
                    if not p.is_file() or scanner.is_binary(p):
                        continue
                    file_findings, _, _ = scanner.scan_file("git-staged", p, args.llm)
                    findings.extend(file_findings)

                if not findings:
                    print(f"[Maskara] {len(staged_files)} staged file(s) checked. 100% clean.")
                    return 0

                print(f"[Maskara] Found {len(findings)} sensitive value(s) in staged files:")
                for f in findings:
                    print(
                        f"  - {f['file']}:{f['line']} | {f['rule_name']} ({f['severity']}) | Preview: {f['preview']}"
                    )
                return (
                    1
                    if any(f["severity"] in ("critical", "high", "medium") for f in findings)
                    else 0
                )

            elif getattr(args, "files", None):
                findings = []
                for fpath_str in args.files:
                    p = Path(fpath_str)
                    if not p.is_file() or scanner.is_binary(p):
                        continue
                    file_findings, _, _ = scanner.scan_file("batch-file", p, args.llm)
                    findings.extend(file_findings)

                if not findings:
                    print(f"[Maskara] {len(args.files)} file(s) checked. 100% clean.")
                    return 0

                print(f"[Maskara] Found {len(findings)} sensitive value(s):")
                for f in findings:
                    print(
                        f"  - {f['file']}:{f['line']} | {f['rule_name']} ({f['severity']}) | Preview: {f['preview']}"
                    )
                return (
                    1
                    if any(f["severity"] in ("critical", "high", "medium") for f in findings)
                    else 0
                )

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
                1
                if any(f["severity"] in ("critical", "high", "medium") for f in result["findings"])
                else 0
            )

        elif cmd == "init-hooks":
            import subprocess

            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    timeout=5,
                )
                if res.returncode != 0:
                    err_msg = res.stderr.decode("utf-8", errors="replace").strip()
                    print(
                        f"[Maskara Error] Not inside a Git repository. Cannot initialize hooks: {err_msg}",
                        file=sys.stderr,
                    )
                    return 2
                git_root = Path(res.stdout.decode("utf-8", errors="replace").strip())
            except FileNotFoundError:
                print("[Maskara Error] 'git' command not found. Fail-closed.", file=sys.stderr)
                return 2

            # Check existing core.hooksPath
            cfg_check = subprocess.run(
                ["git", "config", "core.hooksPath"],
                capture_output=True,
                cwd=str(git_root),
            )
            existing_hookspath = cfg_check.stdout.decode("utf-8", errors="replace").strip()
            if (
                existing_hookspath
                and existing_hookspath != ".githooks"
                and not getattr(args, "force", False)
            ):
                print(
                    f"⚠️ [Maskara Warning] Existing core.hooksPath detected: '{existing_hookspath}'\n"
                    "Use --force to overwrite with '.githooks'.",
                    file=sys.stderr,
                )
                return 1

            hooks_dir = git_root / ".githooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            pre_commit_path = hooks_dir / "pre-commit"

            hook_content = (
                "#!/bin/sh\n"
                "# ==============================================================================\n"
                "# CCBA Client-Side Guardrail: Maskara Secret & Privacy Leak Pre-Commit Scan\n"
                "# Reference: CCBA-SOP-SEC-001, ADR-0047, Session Learning #41\n"
                "# ==============================================================================\n"
                'echo "🔍 [CCBA Guardrail] Running Maskara staged files scanner..."\n\n'
                "if command -v maskara >/dev/null 2>&1; then\n"
                "  maskara scan --staged\n"
                'elif [ -x ".venv/bin/python" ] && .venv/bin/python -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  .venv/bin/python -m ccba_maskara.cli scan --staged\n"
                'elif [ -x "scripts/.venv/bin/python" ] && scripts/.venv/bin/python -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  scripts/.venv/bin/python -m ccba_maskara.cli scan --staged\n"
                'elif [ -x ".venv/Scripts/python.exe" ] && .venv/Scripts/python.exe -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  .venv/Scripts/python.exe -m ccba_maskara.cli scan --staged\n"
                'elif [ -x "scripts/.venv/Scripts/python.exe" ] && scripts/.venv/Scripts/python.exe -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  scripts/.venv/Scripts/python.exe -m ccba_maskara.cli scan --staged\n"
                'elif command -v python3 >/dev/null 2>&1 && python3 -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  python3 -m ccba_maskara.cli scan --staged\n"
                'elif command -v python >/dev/null 2>&1 && python -c "import ccba_maskara" >/dev/null 2>&1; then\n'
                "  python -m ccba_maskara.cli scan --staged\n"
                "else\n"
                '  echo "❌ [CCBA Guardrail Error] ccba-maskara CLI not found. Please install: pip install ccba-maskara" >&2\n'
                '  echo "💡 [Bypass khẩn cấp]: git commit --no-verify" >&2\n'
                "  exit 1\n"
                "fi\n"
            )

            pre_commit_path.write_bytes(hook_content.encode("utf-8"))
            try:
                pre_commit_path.chmod(0o755)
            except Exception:
                pass

            subprocess.run(
                ["git", "update-index", "--chmod=+x", ".githooks/pre-commit"],
                cwd=str(git_root),
                capture_output=True,
            )

            # Ensure .gitattributes has .githooks/* text eol=lf (idempotent)
            gitattributes_path = git_root / ".gitattributes"
            attr_line = ".githooks/* text eol=lf\n"
            existing_attrs = ""
            if gitattributes_path.is_file():
                existing_attrs = gitattributes_path.read_text(encoding="utf-8")
            if ".githooks/* text eol=lf" not in existing_attrs:
                with gitattributes_path.open("a", encoding="utf-8") as attr_file:
                    if existing_attrs and not existing_attrs.endswith("\n"):
                        attr_file.write("\n")
                    attr_file.write(attr_line)

            subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=str(git_root),
                check=True,
            )
            print(
                "✅ [Maskara] Successfully installed .githooks/pre-commit and configured core.hooksPath=.githooks"
            )
            return 0

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
