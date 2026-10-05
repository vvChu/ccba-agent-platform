"""packages/ccba-harness/tests/test_peer_dispatch_cli.py - Unit tests for peer-dispatch CLI.

Validates Level-2 peer dispatch flags, dry-run output, and error handling (ADR-0063).
"""

from __future__ import annotations

from ccba_harness.cli import main, run_peer_dispatch_cli
from ccba_harness.peer import PeerPromptEnvelope, render_prompt_header


def test_peer_dispatch_missing_prompt_fails(capsys):
    ret = run_peer_dispatch_cli(["--prompt-file", "/non/existent/prompt.md"])
    assert ret == 1
    err = capsys.readouterr().err
    assert "[FAIL] Prompt file not found" in err


def test_peer_dispatch_dry_run_with_profile(tmp_path, capsys):
    prompt = tmp_path / "prompt_test.md"
    envelope = PeerPromptEnvelope(
        request_id="req-dry-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Dry run test",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    ret = run_peer_dispatch_cli(
        [
            "--prompt-file",
            str(prompt),
            "--profile",
            "agentic_code",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Profile: agentic_code" in out
    assert "[DRY-RUN] Model: grok-4.7-build-fast" in out
    assert "[DRY-RUN] Max Turns: 8" in out
    assert "--max-turns 8" in out


def test_peer_dispatch_dry_run_with_tier_local(tmp_path, capsys):
    prompt = tmp_path / "prompt_test.md"
    envelope = PeerPromptEnvelope(
        request_id="req-dry-002",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Tier Local Test",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    ret = run_peer_dispatch_cli(
        [
            "--prompt-file",
            str(prompt),
            "--tier",
            "local",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Model: qwen-local" in out


def test_main_fast_dispatch_peer_dispatch(tmp_path, capsys):
    prompt = tmp_path / "prompt_test.md"
    envelope = PeerPromptEnvelope(
        request_id="req-dry-003",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Fast Dispatch Test",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    ret = main(["peer-dispatch", "--prompt-file", str(prompt), "--dry-run"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Command:" in out


def test_scripts_peer_dispatch_delegation(tmp_path, capsys):
    from scripts.peer_dispatch import main as script_main

    prompt = tmp_path / "prompt_test.md"
    envelope = PeerPromptEnvelope(
        request_id="req-dry-004",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Script Delegation Test",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    ret = script_main(["--prompt-file", str(prompt), "--dry-run"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Command:" in out
