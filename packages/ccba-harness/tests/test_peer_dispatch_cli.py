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


def test_peer_dispatch_dry_run_with_audit_direct_and_no_tools(tmp_path, capsys):
    prompt = tmp_path / "prompt_direct.md"
    envelope = PeerPromptEnvelope(
        request_id="req-dry-005",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Audit Direct Test",
        timestamp="2026-10-07T21:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    # 1. Profile audit_direct
    ret = run_peer_dispatch_cli(
        [
            "--prompt-file",
            str(prompt),
            "--profile",
            "audit_direct",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Profile: audit_direct" in out
    assert "[DRY-RUN] Max Turns: 3" in out
    assert "--deny *" in out

    # 2. Flag --no-tools with arch_audit (should override tools and cap max-turns to 3)
    ret = run_peer_dispatch_cli(
        [
            "--prompt-file",
            str(prompt),
            "--profile",
            "arch_audit",
            "--no-tools",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Profile: arch_audit" in out
    assert "[DRY-RUN] Max Turns: 3" in out
    assert "--deny *" in out


def test_peer_dispatch_cli_deep_spec_audit_and_signoff_diff_resume(tmp_path, capsys):
    prompt = tmp_path / "prompt_signoff.md"
    envelope = PeerPromptEnvelope(
        request_id="req-cli-005",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Signoff Diff Test",
        timestamp="2026-10-17T20:00:00+07:00",
        output_path="out.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    ret = run_peer_dispatch_cli(
        [
            "--prompt-file",
            str(prompt),
            "--profile",
            "signoff_diff",
            "--resume",
            "01a148d0-ac92-7ef2-a970-efb8c8fe1aed",
            "--fork-session",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] Profile: signoff_diff" in out
    assert "[DRY-RUN] Max Turns: 15" in out
    assert "--output-format json" in out
    assert "--resume 01a148d0-ac92-7ef2-a970-efb8c8fe1aed --fork-session" in out
    assert "--verbatim" in out
    assert "--disable-web-search" in out


def test_peer_dispatch_default_spec_lockdown_and_summary_output(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt_no_profile.md"
    envelope = PeerPromptEnvelope(
        request_id="req-cli-default-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="discuss",
        subject="Default Spec Lockdown Test",
        timestamp="2026-10-18T18:50:00+07:00",
        output_path="grok_no_profile.md",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    # 1. Dry-run without profile should enforce DEFAULT_GROK_SPEC read-only lockdown
    ret_dry = run_peer_dispatch_cli(["--prompt-file", str(prompt), "--dry-run"])
    assert ret_dry == 0
    out_dry = capsys.readouterr().out
    assert "--verbatim" in out_dry
    assert "--disable-web-search" in out_dry
    assert "--tools read_file,grep,list_dir" in out_dry

    # 2. Live execution prints [PEER-SUMMARY] line with Verdict, Risk, Blocking Conditions, Session ID
    out_file = tmp_path / "grok_no_profile.md"
    out_file.write_text(
        "---\nrequest_id: req-cli-default-001\nverdict: APPROVE_WITH_CONDITIONS\nrisk_score: 2\n"
        "conditions:\n  - id: COND-01\n    description: Check A\n    blocking: true\n"
        "telemetry:\n  session_id: sess-sum-123\n  primary_model: grok-4.7\n"
        "  input_tokens: 100\n  output_tokens: 50\n  total_tokens: 150\n---\n# Done\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("ccba_harness.peer.invoke_grok_cli", lambda **kw: True)
    ret_live = run_peer_dispatch_cli(["--prompt-file", str(prompt)])
    assert ret_live == 0
    out_live = capsys.readouterr().out
    assert "[OK] Peer dispatch completed successfully with valid verdict." in out_live
    assert (
        "[PEER-SUMMARY] Verdict: APPROVE_WITH_CONDITIONS | Risk: 2 | Blocking Conditions: 1 | Session ID: sess-sum-123"
        in out_live
    )
