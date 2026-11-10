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
    assert "[DRY-RUN] Max Turns: 8" in out
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


def test_parse_envelope_tolerant_normalization_and_reverify_suffix(tmp_path):
    """Validates tolerant frontmatter normalization and -reverify/-signoff suffix session discovery."""
    from ccba_harness._peer_watchdog import _resolve_grok_profile_options
    from ccba_harness.peer import (
        PROFILE_SPECS,
        PeerVerdictBlock,
        PeerVerdictTelemetry,
        parse_envelope_from_md,
        render_verdict_header,
    )

    raw_md = (
        "---\n"
        "task_id: req-20261108-ai-eos-ch08-v2-reverify\n"
        "task_type: architectural_and_editorial_review\n"
        "question: Final re-verification for Chapter 8\n"
        "session_id: sess-stage1\n"
        "stage: 3\n"
        "schema_version: '1.0'\n"
        "issue_ref: '#108'\n"
        "---\n# Body\n"
    )
    prompt_p = tmp_path / "prompt_grok_review_chuong_8_v2_reverify.md"
    env = parse_envelope_from_md(raw_md, prompt_path=prompt_p)
    assert env is not None
    assert env.request_id == "req-20261108-ai-eos-ch08-v2-reverify"
    assert env.from_agent == "antigravity"
    assert env.to_agent == "grok"
    assert env.request_type == "review"
    assert env.subject == "Final re-verification for Chapter 8"
    assert env.resume_session_id == "sess-stage1"
    assert env.fork_session is True
    assert env.output_path == "grok_review_chuong_8_v2_reverify.md"

    # Verify -v2-reverify auto-discovers session from -v2 verdict when resume_session_id is omitted
    v2_verdict = PeerVerdictBlock(
        request_id="req-20261108-ai-eos-ch08-v2",
        verdict="APPROVE_WITH_CONDITIONS",
        summary="v2 review",
        telemetry=PeerVerdictTelemetry(
            session_id="sess-ch08-v2",
            primary_model="grok-4.7",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            turn_count=2,
            cost_usd=0.01,
        ),
    )
    (tmp_path / "grok_review_chuong_8_v2.md").write_text(
        render_verdict_header(v2_verdict) + "\n# V2", encoding="utf-8"
    )
    raw_reverify = (
        "---\n"
        "request_id: req-20261108-ai-eos-ch08-v2-reverify\n"
        "request_type: signoff\n"
        "chapter: Chapter 8 Reverify\n"
        "---\nShort delta\n"
    )
    prompt_p.write_text(raw_reverify, encoding="utf-8")
    env_rev = parse_envelope_from_md(raw_reverify, prompt_path=prompt_p)
    assert env_rev is not None
    assert env_rev.request_type == "review"
    opts = _resolve_grok_profile_options(
        PROFILE_SPECS["audit_direct"], env_rev, None, None, False, None, None, prompt_p
    )
    assert opts["resume_session_id"] == "sess-ch08-v2"

    # Verify historical transcript edge cases: sender/recipient/context_files, dict source_documents, profile alias
    raw_edge = (
        "---\n"
        "id: req-review-pr-576\n"
        "sender: antigravity\n"
        "recipient: grok\n"
        "type: ARCHITECTURE_REVIEW\n"
        "profile: code_audit\n"
        "source_documents:\n"
        "  - path: tools/eos/drift.py\n"
        "    role: drift validator\n"
        "---\nBody\n"
    )
    env_edge = parse_envelope_from_md(raw_edge, prompt_path=tmp_path / "prompt_grok_pr_576.md")
    assert env_edge is not None
    assert env_edge.request_id == "req-review-pr-576"
    assert env_edge.from_agent == "antigravity"
    assert env_edge.to_agent == "grok"
    assert env_edge.request_type == "review"
    assert env_edge.profile == "code_review"
    assert env_edge.source_documents == ["tools/eos/drift.py"]


def test_peer_dispatch_output_file_flag_and_preflight_envelope_error(tmp_path, capsys):
    """Validates -o/--output-file flag and [PREFLIGHT-ENVELOPE-ERROR] diagnostic on missing frontmatter."""
    from ccba_harness.peer import invoke_grok_cli

    bad_prompt = tmp_path / "prompt_no_frontmatter.md"
    bad_prompt.write_text("# Just markdown without YAML frontmatter\n", encoding="utf-8")
    assert invoke_grok_cli(bad_prompt) is False
    err = capsys.readouterr().err
    assert "[PREFLIGHT-ENVELOPE-ERROR]" in err
    assert "prompt_no_frontmatter.md" in err

    valid_prompt = tmp_path / "prompt_custom_out.md"
    valid_prompt.write_text(
        "---\nrequest_id: req-out-flag\nsubject: Custom out\n---\nBody\n",
        encoding="utf-8",
    )
    custom_out = tmp_path / "custom_verdict.md"
    ret = run_peer_dispatch_cli(
        ["--prompt-file", str(valid_prompt), "-o", str(custom_out), "--dry-run"]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert f"[DRY-RUN] Expected Output: {custom_out.resolve()}" in out


def test_peer_dispatch_cli_flag_aliases_and_minimal_frontmatter(tmp_path, capsys):
    """Validates -p/--prompt, --output/--response-file, --session-id/--session aliases and minimal frontmatter."""
    from ccba_harness.peer import parse_envelope_from_md, scan_peer_exchange

    min_prompt = tmp_path / "prompt_grok_wave3_signoff.md"
    min_prompt.write_text(
        "---\n"
        "author: antigravity\n"
        "target: grok\n"
        "request_type: signoff\n"
        "wave: Wave 3 Architecture Sign-Off\n"
        "session_id: 162a3e2c-9415-4a41-a219-f27a1d88bc2f\n"
        "target_scope:\n"
        "  - packages/ccba-harness/src/ccba_harness/peer.py\n"
        "---\nBody\n",
        encoding="utf-8",
    )
    env = parse_envelope_from_md(min_prompt.read_text(encoding="utf-8"), prompt_path=min_prompt)
    assert env is not None
    assert env.request_id == "prompt_grok_wave3_signoff"
    assert env.from_agent == "antigravity"
    assert env.to_agent == "grok"
    assert env.subject == "Wave 3 Architecture Sign-Off"
    assert env.resume_session_id == "162a3e2c-9415-4a41-a219-f27a1d88bc2f"
    assert env.target_files == ["packages/ccba-harness/src/ccba_harness/peer.py"]

    # scan_peer_exchange passes prompt_path=path so minimal frontmatter without request_id is parsed
    _, _, reg = scan_peer_exchange(tmp_path, {})
    assert reg["prompt_grok_wave3_signoff.md"]["envelope"] is not None

    out_path = tmp_path / "response_grok_wave3_signoff.md"
    ret = run_peer_dispatch_cli(
        [
            "-p",
            str(min_prompt),
            "--output",
            str(out_path),
            "--session-id",
            "162a3e2c-9415-4a41-a219-f27a1d88bc2f",
            "--profile",
            "signoff_diff",
            "--dry-run",
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert f"[DRY-RUN] Expected Output: {out_path.resolve()}" in out
    assert "--resume 162a3e2c-9415-4a41-a219-f27a1d88bc2f" in out

    # Verify fenced ```yaml PeerVerdictBlock / peer_verdict unwrapping without --- delimiters
    from ccba_harness.peer import parse_verdict_from_md

    fenced_verdict = (
        "Preamble text before code fence.```yaml\n"
        "PeerVerdictBlock:\n"
        "  request_id: req-fenced-01\n"
        "  verdict: APPROVE_WITH_CONDITIONS\n"
        "  risk_score: 6\n"
        "  summary: Fenced YAML verdict\n"
        "telemetry:\n"
        "  session_id: sess-fenced-01\n"
        "  primary_model: grok-4.7\n"
        "```\n# Detailed Analysis\n"
    )
    vb = parse_verdict_from_md(fenced_verdict)
    assert vb is not None
    assert vb.request_id == "req-fenced-01"
    assert vb.verdict == "APPROVE_WITH_CONDITIONS"
    assert vb.risk_score == 3
    assert vb.telemetry is not None and vb.telemetry.session_id == "sess-fenced-01"
