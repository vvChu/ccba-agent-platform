"""commands/verifier.py - CLI handlers for verify-patch and verify-doc commands (ADR-0058)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ccba_harness.cli._envelope import (
    build_invalid_input_envelope,
    enrich_doc_result_dict,
    enrich_patch_report_dict,
    parse_with_json_envelope,
    resolve_exit_code,
)


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


def _configure_win32_utf8_stdio() -> None:
    """Ensure UTF-8 stdout/stderr encoding on Windows terminals."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass


def _execute_verify_doc(args: argparse.Namespace) -> int:
    """Execute document artifact check and emit text or JSON output."""
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
    if args.json:
        payload = enrich_doc_result_dict(result, args.target, args.min_bytes, headings)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        err_code = None if result.passed else "CHECKS_FAILED"
        return resolve_exit_code(
            passed=result.passed, semantic=args.semantic_exit_codes, error_code=err_code
        )

    if result.passed:
        if result.stdout:
            print(result.stdout)
        return 0
    print(f"ERROR: {result.error_message}", file=sys.stderr)
    return 1


def run_verify_doc_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic document artifact verification."""
    _configure_win32_utf8_stdio()
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
        "--cwd", type=str, default=None, help="Base working directory to resolve relative paths"
    )
    parser.add_argument("--json", action="store_true", help="Output result in JSON format")
    parser.add_argument(
        "--semantic-exit-codes",
        action="store_true",
        help="Return semantic exit codes (0|1|2|4|124)",
    )

    args, parse_err = parse_with_json_envelope(parser, args_list)
    if args is None:
        return parse_err if parse_err is not None else 2
    return _execute_verify_doc(args)


def _resolve_patch_commands(args: argparse.Namespace, *, quiet: bool = False) -> list[str] | None:
    """Resolves commands from CLI args, positional args, and --file."""
    commands_to_run: list[str] = []
    if args.commands:
        commands_to_run.extend(args.commands)
    if args.pos_commands:
        commands_to_run.extend(args.pos_commands)
    if args.file:
        f_path = Path(args.file)
        if not f_path.exists():
            if not quiet:
                print(f"ERROR: Commands file does not exist: {f_path}", file=sys.stderr)
            return None
        commands_to_run.extend(_parse_commands_from_file(f_path))
    if not commands_to_run and not args.preset:
        if not quiet:
            print("ERROR: No commands or preset specified for verification.", file=sys.stderr)
        return None
    return commands_to_run


def _emit_invalid_patch_input(
    args: argparse.Namespace, message: str, *, already_printed: bool = False
) -> int:
    """Emit INVALID_INPUT JSON or stderr message without creating --report-file."""
    if args.json:
        payload = build_invalid_input_envelope(
            message,
            "ccba-harness verify-patch --help",
            "Provide --cmd, --file, or --preset with required options",
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif not already_printed:
        print(f"ERROR: {message}", file=sys.stderr)
    return resolve_exit_code(
        passed=False,
        semantic=getattr(args, "semantic_exit_codes", False),
        error_code="INVALID_INPUT",
    )


def _emit_verify_patch_output(
    report: Any, healing_report: Any | None, args: argparse.Namespace
) -> int:
    """Writes optional report file and prints verification output to stdout."""
    active = healing_report if healing_report else report
    base_dir = Path(args.cwd).resolve() if getattr(args, "cwd", None) else None
    enriched, err_code = enrich_patch_report_dict(active.to_dict(), report, base_dir=base_dir)
    if args.report_file:
        rf_path = Path(args.report_file)
        rf_path.parent.mkdir(parents=True, exist_ok=True)
        if rf_path.suffix.lower() == ".json":
            rf_path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            rf_path.write_text(active.to_markdown(), encoding="utf-8")

    if args.json:
        print(json.dumps(enriched, indent=2, ensure_ascii=False))
    else:
        print(active.to_markdown())
    return resolve_exit_code(
        passed=bool(report.all_passed),
        semantic=getattr(args, "semantic_exit_codes", False),
        error_code=err_code,
    )


def _add_patch_execution_args(parser: argparse.ArgumentParser) -> None:
    """Register command-source and output flags for verify-patch."""
    parser.add_argument(
        "pos_commands", nargs="*", default=[], help="Command strings to execute sequentially"
    )
    parser.add_argument(
        "-c",
        "--cmd",
        "--commands",
        dest="commands",
        action="extend",
        nargs="+",
        default=None,
        help="Command string(s) to execute",
    )
    parser.add_argument(
        "--file", type=str, default=None, help="Path to a text or JSON file containing commands"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Per-command execution timeout in seconds (default: 180.0)",
    )
    parser.add_argument(
        "--cwd", type=str, default=None, help="Working directory for command execution"
    )
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failing command")
    parser.add_argument("--json", action="store_true", help="Output full result in JSON format")
    parser.add_argument(
        "--semantic-exit-codes",
        action="store_true",
        help="Return semantic exit codes (0|1|2|4|124)",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write markdown or JSON verification report to path",
    )


def _add_patch_preset_args(parser: argparse.ArgumentParser) -> None:
    """Register preset and self-healing flags for verify-patch."""
    parser.add_argument(
        "--preset",
        type=str,
        choices=["code", "doc", "skill", "adr", "telemetry", "ci", "eval", "lexicon"],
        default=None,
        help="Verification preset to automatically generate standard check commands",
    )
    parser.add_argument(
        "--target", type=str, default=None, help="Target file or directory path for the preset"
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


def _build_verify_patch_parser() -> argparse.ArgumentParser:
    """Build ArgumentParser for `ccba-harness verify-patch`."""
    parser = argparse.ArgumentParser(
        prog="ccba-harness verify-patch",
        description="Verify patches & code changes deterministically via CLI exit codes.",
    )
    _add_patch_execution_args(parser)
    _add_patch_preset_args(parser)
    return parser


def _execute_verify_patch(args: argparse.Namespace) -> int:
    """Execute verification commands, optional self-healing, and emit report."""
    commands_to_run = _resolve_patch_commands(args, quiet=bool(args.json))
    if commands_to_run is None:
        return _emit_invalid_patch_input(
            args, "No commands or preset specified for verification.", already_printed=not args.json
        )

    from ccba_harness.verifier import verify_patch_execution

    headings = (
        [h.strip() for h in args.required_headings.split(",") if h.strip()]
        if args.required_headings
        else None
    )
    try:
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
    except ValueError as exc:
        return _emit_invalid_patch_input(args, str(exc))

    healing_report = None
    if not report.all_passed and args.self_heal:
        from ccba_harness.healing import SelfHealingEngine

        target_base = Path(args.cwd).resolve() if args.cwd else Path.cwd()
        engine = SelfHealingEngine(base_dir=target_base, max_iterations=args.max_heal_iterations)
        healing_report = engine.attempt_closed_loop_healing(
            verify_commands=[r.command for r in report.results], timeout=args.timeout
        )
        if healing_report.final_verification_report:
            report = healing_report.final_verification_report
    return _emit_verify_patch_output(report, healing_report, args)


def run_verify_patch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic patch verification (`ccba-harness verify-patch`)."""
    _configure_win32_utf8_stdio()
    parser = _build_verify_patch_parser()
    args, parse_err = parse_with_json_envelope(parser, args_list)
    if args is None:
        return parse_err if parse_err is not None else 2
    return _execute_verify_patch(args)
