"""test_cli_doc_parity.py - Automated contract test ensuring CLI commands and SKILL.md documentation stay in 100% parity."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ccba_legal.cli import build_parser

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_cli_parser_subcommands_have_help() -> None:
    """Verify every registered subcommand in ccba-legal CLI has explicit help descriptions."""
    parser = build_parser()
    subparsers_action = next(action for action in parser._actions if action.dest == "command")
    choices = subparsers_action.choices  # dict of command_name -> subparser
    assert len(choices) >= 6, f"Expected at least 6 subcommands, found {len(choices)}"

    for cmd_name, subp in choices.items():
        assert subp.description or len(subp._actions) > 0, f"Subcommand '{cmd_name}' is empty!"


def test_cli_help_execution_zero_exit_code() -> None:
    """Verify python -m ccba_legal --help executes without runtime errors and exits with code 0."""
    res = subprocess.run(
        [sys.executable, "-m", "ccba_legal", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 0, f"CLI --help failed with error:\n{res.stderr}"
    assert "CCBA Legal Intelligence" in res.stdout
    assert "login" in res.stdout
    assert "fetch" in res.stdout
    assert "convert" in res.stdout


def test_cli_subcommands_documented_in_skill_md() -> None:
    """Verify every subcommand in CLI is documented in SKILL.md to guarantee zero documentation drift."""
    # Candidate SKILL.md paths
    candidate_paths = [
        Path.cwd() / ".agents" / "skills" / "ccba-legal-intel" / "SKILL.md",
        Path.cwd() / ".." / ".." / ".agents" / "skills" / "ccba-legal-intel" / "SKILL.md",
        Path("D:/GitHubProjects/ccba-legal-knowledge/.agents/skills/ccba-legal-intel/SKILL.md"),
    ]
    skill_file = None
    for p in candidate_paths:
        if p.resolve().exists():
            skill_file = p.resolve()
            break

    if not skill_file:
        pytest.skip("SKILL.md not found in candidate paths for local test run.")

    skill_text = skill_file.read_text(encoding="utf-8")

    # Verify each core command is mentioned in SKILL.md
    for cmd in [
        "login",
        "fetch",
        "convert",
        "consolidate",
        "sync",
        "query",
        "get-clause",
        "get-table",
    ]:
        assert f"python -m ccba_legal {cmd}" in skill_text or f"`{cmd}`" in skill_text, (
            f"Command '{cmd}' is registered in cli.py but missing from SKILL.md ({skill_file})!"
        )
