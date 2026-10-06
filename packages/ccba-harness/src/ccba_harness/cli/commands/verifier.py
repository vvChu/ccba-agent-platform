"""commands/verifier.py - CLI handlers for verify-patch and verify-doc commands (ADR-0058)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


def _parse_commands_from_file(file_path: Path) -> list[str]:
    """Parse list of commands from a text or JSON file."""
    import json

    content = file_path.read_text(encoding="utf-8").strip()
    commands: list[str] = []
    if content.startswith("["):
        try:
            loaded = json.loads(content)
            if isinstance(loaded, list):
                commands.extend(str(item).strip() for item in loaded if item)
        except Exception as err:
            print(f"ERROR: Failed to parse JSON commands file: {err}", file=sys.stderr)
            return []
    else:
        for line in content.splitlines():
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#"):
                commands.append(cleaned)
    return commands


def run_verify_doc_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic document artifact verification."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        prog="ccba-harness verify-doc",
        description="Verify a document artifact's presence, size, and headings contract.",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to the document artifact (.md, .docx, .pptx, etc.)",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=100,
        help="Minimum expected file size in bytes (default: 100)",
    )
    parser.add_argument(
        "--required-headings",
        type=str,
        default=None,
        help="Comma-separated list of heading titles required in markdown",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Base working directory to resolve relative paths",
    )

    args = parser.parse_args(args_list)

    from ccba_harness.verifier import verify_document_artifact

    headings = (
        [h.strip() for h in args.required_headings.split(",") if h.strip()]
        if args.required_headings
        else None
    )

    result = verify_document_artifact(
        target_path=args.target,
        min_bytes=args.min_bytes,
        required_headings=headings,
        cwd=args.cwd,
    )

    if result.passed:
        if result.stdout:
            print(result.stdout)
        return 0
    else:
        print(f"ERROR: {result.error_message}", file=sys.stderr)
        return 1


def run_verify_patch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic patch verification (`ccba-harness verify-patch`)."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        prog="ccba-harness verify-patch",
        description="Verify patches & code changes deterministically via CLI exit codes.",
    )
    parser.add_argument(
        "pos_commands",
        nargs="*",
        default=[],
        help="Command strings to execute sequentially",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        "--commands",
        dest="commands",
        nargs="+",
        default=[],
        help="Command string(s) to execute",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a text or JSON file containing commands",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Per-command execution timeout in seconds (default: 180.0)",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Working directory for command execution",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failing command",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full result in JSON format",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write markdown or JSON verification report to path",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["code", "doc", "skill", "adr", "telemetry", "ci", "eval"],
        default=None,
        help="Verification preset to automatically generate standard check commands",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target file or directory path for the preset",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=100,
        help="Minimum expected bytes for 'doc' preset (default: 100)",
    )
    parser.add_argument(
        "--required-headings",
        type=str,
        default=None,
        help="Comma-separated required headings for 'doc' preset",
    )
    parser.add_argument(
        "--self-heal",
        action="store_true",
        help="Enable autonomous self-healing for fixable format, lint, and metadata drift errors",
    )
    parser.add_argument(
        "--max-heal-iterations",
        type=int,
        default=2,
        help="Maximum self-healing loop iterations (default: 2)",
    )

    args = parser.parse_args(args_list)

    commands_to_run: list[str] = []
    if args.commands:
        commands_to_run.extend(args.commands)
    if args.pos_commands:
        commands_to_run.extend(args.pos_commands)

    if args.file:
        f_path = Path(args.file)
        if not f_path.exists():
            print(f"ERROR: Commands file does not exist: {f_path}", file=sys.stderr)
            return 1
        parsed_cmds = _parse_commands_from_file(f_path)
        commands_to_run.extend(parsed_cmds)

    if not commands_to_run and not args.preset:
        print("ERROR: No commands or preset specified for verification.", file=sys.stderr)
        return 1

    headings = (
        [h.strip() for h in args.required_headings.split(",") if h.strip()]
        if args.required_headings
        else None
    )

    from ccba_harness.verifier import verify_patch_execution

    report = verify_patch_execution(
        commands=commands_to_run,
        preset=args.preset,
        target=args.target,
        min_bytes=args.min_bytes,
        required_headings=headings,
        cwd=Path(args.cwd).resolve() if args.cwd else None,
        timeout=args.timeout,
        fail_fast=args.fail_fast,
    )

    healing_report = None
    if not report.all_passed and args.self_heal:
        from ccba_harness.healing import SelfHealingEngine

        target_base = Path(args.cwd).resolve() if args.cwd else Path.cwd()
        engine = SelfHealingEngine(base_dir=target_base, max_iterations=args.max_heal_iterations)
        cmds_to_heal = [r.command for r in report.results]
        healing_report = engine.attempt_closed_loop_healing(
            verify_commands=cmds_to_heal,
            timeout=args.timeout,
        )
        if healing_report.final_verification_report:
            report = healing_report.final_verification_report

    if args.report_file:
        import json

        rf_path = Path(args.report_file)
        rf_path.parent.mkdir(parents=True, exist_ok=True)
        if rf_path.suffix.lower() == ".json":
            data_to_write = healing_report.to_dict() if healing_report else report.to_dict()
            rf_path.write_text(
                json.dumps(data_to_write, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        else:
            text_to_write = healing_report.to_markdown() if healing_report else report.to_markdown()
            rf_path.write_text(text_to_write, encoding="utf-8")

    if args.json:
        import json

        data_to_print = healing_report.to_dict() if healing_report else report.to_dict()
        print(json.dumps(data_to_print, indent=2, ensure_ascii=False))
    else:
        if healing_report:
            print(healing_report.to_markdown())
        else:
            print(report.to_markdown())

    return 0 if report.all_passed else 1
