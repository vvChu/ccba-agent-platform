"""test_cli_contract_parity.py - Contract parity test suite for ccba-harness CLI.

Locks down:
1. All 13 primary subcommands and their fast-path / argparse aliases.
2. The 3 supported invocation entry points:
   - Entry point 1: ccba_harness.cli:main
   - Entry point 2: python -m ccba_harness
   - Entry point 3: python -m ccba_harness.cli
3. All public symbols exported and expected by external consumers.
4. Mock patch compatibility with unittest.mock.patch.
"""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import pytest

import ccba_harness.cli as cli_module
from ccba_harness.cli import (
    main,
)

ALL_SUBCOMMAND_INVOCATIONS = [
    # Primary subcommands
    ["validate-skill", "--help"],
    ["evaluate-gpi", "--help"],
    ["eval", "--help"],
    ["verify-patch", "--help"],
    ["verify-doc", "--help"],
    ["telemetry", "--help"],
    ["peer-gate", "--help"],
    ["peer-watch", "--help"],
    ["peer-dispatch", "--help"],
    ["peer-co-review", "--help"],
    ["apply-anchor-patch", "--help"],
    ["blast-radius", "--help"],
    ["why", "--help"],
    # Fast-path and argparse aliases
    ["gate", "--help"],
    ["watch-peer", "--help"],
    ["dispatch-peer", "--help"],
    ["co-review", "--help"],
    ["peer-apply", "--help"],
    ["apply-patch", "--help"],
    ["explain-why", "--help"],
]


@pytest.mark.parametrize("subcmd_args", ALL_SUBCOMMAND_INVOCATIONS)
def test_all_subcommands_and_aliases_help(subcmd_args: list[str]) -> None:
    """Verifies that every primary subcommand and alias exits 0 on --help."""
    try:
        ret = main(subcmd_args)
    except SystemExit as exc:
        ret = exc.code
    assert ret == 0, f"Subcommand {subcmd_args[0]} failed to return 0 on --help"


def test_root_help_and_empty_args() -> None:
    """Verifies root main with empty args or --help returns 0."""
    assert main([]) == 0
    try:
        ret = main(["--help"])
    except SystemExit as exc:
        ret = exc.code
    assert ret == 0


def test_three_entry_points_parity() -> None:
    """Verifies parity across the three entry points: console, -m ccba_harness, -m ccba_harness.cli."""
    # Entry point 1: main function in Python
    assert main([]) == 0

    # Entry point 2: python -m ccba_harness --help
    p2 = subprocess.run(
        [sys.executable, "-m", "ccba_harness", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert p2.returncode == 0, f"-m ccba_harness failed: {p2.stderr}"
    assert "usage:" in p2.stdout.lower()

    # Entry point 3: python -m ccba_harness.cli --help
    p3 = subprocess.run(
        [sys.executable, "-m", "ccba_harness.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert p3.returncode == 0, f"-m ccba_harness.cli failed: {p3.stderr}"
    assert "usage:" in p3.stdout.lower()


def test_all_expected_symbols_exported() -> None:
    """Verifies that all expected public symbols are directly accessible on ccba_harness.cli."""
    expected_symbols = [
        "main",
        "run_skill_validation_cli",
        "run_evaluate_gpi_cli",
        "run_eval_cli",
        "run_verify_doc_cli",
        "run_verify_patch_cli",
        "run_telemetry_cli",
        "run_peer_gate_cli",
        "run_blast_radius_cli",
        "run_explain_why_cli",
        "run_peer_watch_cli",
        "run_peer_dispatch_cli",
        "run_peer_co_review_cli",
        "run_apply_anchor_patch_cli",
        "find_workspace_root",
        "resolve_peer_exchange_dir",
    ]
    for sym in expected_symbols:
        assert hasattr(cli_module, sym), f"Missing public symbol: {sym}"
        val = getattr(cli_module, sym)
        assert callable(val), f"Symbol {sym} is not callable"


def test_mock_patch_compatibility_on_dispatcher() -> None:
    """Verifies that patch('ccba_harness.cli.run_peer_watch_cli') intercepts main dispatch."""
    with patch("ccba_harness.cli.run_peer_watch_cli", return_value=42) as mock_watch:
        ret = main(["peer-watch", "--test-flag"])
        assert ret == 42
        mock_watch.assert_called_once_with(["--test-flag"])
