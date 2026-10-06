"""core.py - Root ArgumentParser and command dispatcher for ccba-harness CLI.

Provides deterministic routing via an explicit static registry without startup import overhead.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    """Specification for an explicit CLI subcommand."""

    names: tuple[str, ...]
    module: str
    attr: str
    help: str


COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        names=("validate-skill",),
        module="ccba_harness.cli.commands.evals",
        attr="run_skill_validation_cli",
        help="Validate CCBA Agent Skills & Workflows offline/standalone.",
    ),
    CommandSpec(
        names=("evaluate-gpi",),
        module="ccba_harness.cli.commands.evals",
        attr="run_evaluate_gpi_cli",
        help="Evaluate Two-Stage Decision Framework & Granularity Placement Index.",
    ),
    CommandSpec(
        names=("eval",),
        module="ccba_harness.cli.commands.evals",
        attr="run_eval_cli",
        help="Run evaluation benchmarks for skills (CCBA Evals Framework).",
    ),
    CommandSpec(
        names=("verify-patch",),
        module="ccba_harness.cli.commands.verifier",
        attr="run_verify_patch_cli",
        help="Verify patches & code changes deterministically via CLI exit codes.",
    ),
    CommandSpec(
        names=("verify-doc",),
        module="ccba_harness.cli.commands.verifier",
        attr="run_verify_doc_cli",
        help="Verify document artifact presence, size, and headings contract.",
    ),
    CommandSpec(
        names=("telemetry",),
        module="ccba_harness.cli.commands.telemetry",
        attr="run_telemetry_cli",
        help="Subagent runtime telemetry and token monitoring.",
    ),
    CommandSpec(
        names=("peer-gate", "gate"),
        module="ccba_harness.cli.commands.peer",
        attr="run_peer_gate_cli",
        help="Automated 6-stage post-implementation gate verification.",
    ),
    CommandSpec(
        names=("peer-watch", "watch-peer"),
        module="ccba_harness.cli.commands.peer",
        attr="run_peer_watch_cli",
        help="Peer Agent Bridge Watcher and delta synchronizer.",
    ),
    CommandSpec(
        names=("peer-dispatch", "dispatch-peer"),
        module="ccba_harness.cli.commands.peer",
        attr="run_peer_dispatch_cli",
        help="Level-2 Peer Agent Dispatcher and budget guardrail.",
    ),
    CommandSpec(
        names=("peer-co-review", "co-review"),
        module="ccba_harness.cli.commands.peer",
        attr="run_peer_co_review_cli",
        help="Parallel multi-agent co-review orchestration and synthesis.",
    ),
    CommandSpec(
        names=("apply-anchor-patch", "peer-apply", "apply-patch"),
        module="ccba_harness.cli.commands.peer",
        attr="run_apply_anchor_patch_cli",
        help="Apply Level-2 anchor patches with two-phase commit & rollback.",
    ),
    CommandSpec(
        names=("blast-radius",),
        module="ccba_harness.cli.commands.architecture",
        attr="run_blast_radius_cli",
        help="Analyze cross-boundary blast radius and impacted test suites.",
    ),
    CommandSpec(
        names=("why", "explain-why"),
        module="ccba_harness.cli.commands.architecture",
        attr="run_explain_why_cli",
        help="Query architectural rationale from ADRs, git logs & peer exchanges.",
    ),
)

COMMAND_MAP: dict[str, CommandSpec] = {name: spec for spec in COMMANDS for name in spec.names}


def print_root_help() -> None:
    """Prints root help table using explicit static registry."""
    print("usage: ccba-harness [-h] <command> [args...]\n")
    print("CCBA Agent Services Platform — Deterministic Verification Harness.\n")
    print("options:")
    print("  -h, --help    show this help message and exit\n")
    print("commands:")
    for spec in COMMANDS:
        primary = spec.names[0]
        aliases = f" (aliases: {', '.join(spec.names[1:])})" if len(spec.names) > 1 else ""
        print(f"  {primary:<22} {spec.help}{aliases}")


def main(argv: Sequence[str] | None = None) -> int:
    """Root CLI entry point dispatching subcommands via static registry."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass

    args = list(argv) if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print_root_help()
        return 0

    subcmd = args[0]
    spec = COMMAND_MAP.get(subcmd)
    if not spec:
        print(f"ccba-harness: error: invalid choice '{subcmd}'\n", file=sys.stderr)
        print_root_help()
        return 1

    cli_pkg = sys.modules.get("ccba_harness.cli")
    if cli_pkg and hasattr(cli_pkg, spec.attr):
        handler = getattr(cli_pkg, spec.attr)
    else:
        mod = importlib.import_module(spec.module)
        handler = getattr(mod, spec.attr)

    return handler(args[1:])
