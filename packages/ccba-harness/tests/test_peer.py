"""packages/ccba-harness/tests/test_peer.py - Unit tests for Structured Peer Exchange Protocol.

Validates Pydantic v2 schemas, YAML frontmatter extraction, and fail-safe handling (Issue #458).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ccba_harness.peer import (
    PeerCondition,
    PeerPromptEnvelope,
    PeerVerdictBlock,
    atomic_write_text,
    extract_frontmatter,
    flush_pending_peer_triggers,
    invoke_grok_cli,
    load_cache,
    parse_envelope_from_md,
    parse_verdict_from_md,
    publish_peer_message,
    render_prompt_header,
    render_verdict_header,
    save_cache,
    scan_peer_exchange,
)


def test_roundtrip_prompt_envelope():
    envelope = PeerPromptEnvelope(
        request_id="test-req-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Test Code Review",
        timestamp="2026-10-04T16:00:00+07:00",
        source_documents=["docs/adr/0007.md"],
        output_path=".md/peer_exchange/grok_review.md",
        context="Additional notes",
    )
    rendered = render_prompt_header(envelope)
    body = "## Instruction\nPlease review the patch carefully.\n"
    full_content = rendered + body

    parsed = parse_envelope_from_md(full_content)
    assert parsed is not None
    assert parsed.request_id == "test-req-001"
    assert parsed.from_agent == "antigravity"
    assert parsed.to_agent == "grok"
    assert parsed.request_type == "review"
    assert parsed.source_documents == ["docs/adr/0007.md"]


def test_roundtrip_verdict_block():
    verdict = PeerVerdictBlock(
        request_id="test-req-001",
        verdict="GATE_PASS",
        conditions=[
            PeerCondition(id="C1", description="100% tests pass", blocking=True),
            PeerCondition(id="C2", description="Flake8 clean", blocking=False),
        ],
        risk_score=1,
        effort="S",
        summary="All automated checks passed cleanly.",
    )
    rendered = render_verdict_header(verdict)
    body = "### Verification Details\nEverything looks good."
    full_content = rendered + body

    parsed = parse_verdict_from_md(full_content)
    assert parsed is not None
    assert parsed.verdict == "GATE_PASS"
    assert len(parsed.conditions) == 2
    assert parsed.conditions[0].id == "C1"
    assert parsed.conditions[0].blocking is True
    assert parsed.risk_score == 1
    assert parsed.effort == "S"


def test_extra_forbidden_in_envelope():
    data = {
        "request_id": "req-1",
        "from_agent": "antigravity",
        "to_agent": "grok",
        "request_type": "review",
        "subject": "Test",
        "timestamp": "2026-10-04",
        "output_path": "out.md",
        "unknown_extra_field": "disallowed",
    }
    with pytest.raises(ValidationError):
        PeerPromptEnvelope.model_validate(data)


def test_invalid_and_missing_frontmatter_handled_gracefully():
    # 1. Plain markdown without frontmatter
    plain_md = "# Title\n\nJust normal prose text."
    assert parse_envelope_from_md(plain_md) is None
    assert parse_verdict_from_md(plain_md) is None

    data, body = extract_frontmatter(plain_md)
    assert data is None
    assert body == plain_md

    # 2. Malformed frontmatter (syntax error)
    bad_yaml = "---\n: bad: yaml: [}\n---\nBody here"
    assert parse_envelope_from_md(bad_yaml) is None
    assert parse_verdict_from_md(bad_yaml) is None

    # 3. Empty string
    assert parse_envelope_from_md("") is None
    assert parse_verdict_from_md("") is None


def test_publish_peer_message_and_flush(tmp_path):
    envelope = PeerPromptEnvelope(
        request_id="req-pub-1",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Async Publish Test",
        timestamp="2026-10-04T22:00:00+07:00",
        output_path="grok_resp.md",
    )
    hook_called = []
    target = tmp_path / "prompt_grok_test.md"
    published = publish_peer_message(
        envelope, "Body content here", target, on_publish_hook=lambda p: hook_called.append(p)
    )
    assert published.exists()
    assert len(hook_called) == 1
    flush_pending_peer_triggers(timeout=2.0)
    parsed = parse_envelope_from_md(published.read_text(encoding="utf-8"))
    assert parsed is not None
    assert parsed.request_id == "req-pub-1"


def test_seam_mutex_integration(tmp_path):
    cache_file = tmp_path / ".bridge_cache.json"
    save_cache(cache_file, {"file_a.md": "hash123"})
    loaded = load_cache(cache_file)
    assert loaded == {"file_a.md": "hash123"}
    assert cache_file.exists()


def test_recursive_suppression_resilience(tmp_path):
    (tmp_path / "status.json").write_text("{}", encoding="utf-8")
    (tmp_path / "grok_live_summary.md").write_text("# Summary", encoding="utf-8")
    (tmp_path / ".bridge_cache.json").write_text("{}", encoding="utf-8")
    changes, _, _ = scan_peer_exchange(tmp_path, {})
    assert len(changes) == 0


def test_auto_grok_safe_invocation(tmp_path, monkeypatch):
    envelope = PeerPromptEnvelope(
        request_id="req-auto-1",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Auto Grok Invocation Test",
        timestamp="2026-10-04T22:00:00+07:00",
        output_path="grok_auto_resp.md",
    )
    prompt_file = tmp_path / "prompt_grok_auto.md"
    atomic_write_text(prompt_file, render_prompt_header(envelope) + "Please audit.")

    captured_cmds = []

    def mock_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        verdict = PeerVerdictBlock(
            request_id="req-auto-1",
            verdict="APPROVE",
            summary="Auto-grok test passed.",
        )
        stdout = render_verdict_header(verdict) + "Review complete."
        import subprocess

        return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_run)
    success = invoke_grok_cli(prompt_file, model="gemini-38-flash")
    assert success is True
    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    assert "--always-approve" in cmd
    assert "--no-subagents" in cmd
    assert "--reasoning-effort" in cmd
    assert "high" in cmd
    out_file = tmp_path / "grok_auto_resp.md"
    assert out_file.exists()


def test_publish_peer_message_auto_grok(tmp_path, monkeypatch):
    envelope = PeerPromptEnvelope(
        request_id="req-live-auto",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Auto Grok Async Test",
        timestamp="2026-10-04T22:00:00+07:00",
        output_path="grok_async_resp.md",
    )
    prompt_file = tmp_path / "prompt_grok_async.md"

    def mock_run(cmd, **kwargs):
        verdict = PeerVerdictBlock(
            request_id="req-live-auto",
            verdict="APPROVE",
            summary="Async auto-grok completed successfully.",
        )
        stdout = render_verdict_header(verdict) + "Async review content."
        import subprocess

        return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_run)

    publish_peer_message(
        envelope,
        body_text="### Prompt\nPlease review async.",
        target_path=prompt_file,
        auto_grok=True,
    )
    flush_pending_peer_triggers(timeout=5.0)

    out_file = tmp_path / "grok_async_resp.md"
    assert out_file.exists()
    status_file = tmp_path / "status.json"
    assert status_file.exists()
    import json

    data = json.loads(status_file.read_text(encoding="utf-8"))
    assert data["peers"]["grok"]["pending_requests"] == 0
    assert data["peers"]["grok"]["status"] == "idle"
    assert data["peers"]["antigravity"]["status"] == "idle"
    assert len(data["exchange_stats"]["pending_grok"]) == 0


def test_layering_purity():
    import ast
    from pathlib import Path

    peer_py = Path(__file__).resolve().parent.parent / "src" / "ccba_harness" / "peer.py"
    tree = ast.parse(peer_py.read_text(encoding="utf-8"), filename=str(peer_py))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("scripts"), f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("scripts"), f"Forbidden import: {node.module}"


def test_envelope_with_level2_profiles_and_max_turns():
    envelope = PeerPromptEnvelope(
        request_id="req-profile-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="implement",
        subject="Implement feature with Level-2 profile",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="resp.md",
        profile="agentic_code",
        max_turns=8,
        target_files=["packages/foo/src/bar.py"],
    )
    rendered = render_prompt_header(envelope)
    parsed = parse_envelope_from_md(rendered + "Body")
    assert parsed is not None
    assert parsed.profile == "agentic_code"
    assert parsed.max_turns == 8
    assert parsed.target_files == ["packages/foo/src/bar.py"]


def test_build_grok_cmd_mapping(tmp_path):
    from ccba_harness.peer import build_grok_cmd

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Hello", encoding="utf-8")

    cmd = build_grok_cmd(
        prompt_path=prompt,
        model="qwen-local",
        max_turns=1,
        tools=None,
        disallowed_tools=["read_file", "search_replace"],
        reasoning_effort=None,
        worktree=True,
    )
    assert cmd == [
        "grok",
        "-m",
        "qwen-local",
        "--always-approve",
        "--no-subagents",
        "--max-turns",
        "1",
        "--disallowed-tools",
        "read_file,search_replace",
        "--worktree",
        "--prompt-file",
        str(prompt),
    ]


def test_apply_anchor_patch_success(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    target_file = tmp_path / "sample.py"
    initial_content = "def hello():\n    return 'world'\n"
    target_file.write_text(initial_content, encoding="utf-8")
    initial_sha = hashlib.sha256(initial_content.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "sample.py",
                "blob_sha256": initial_sha,
                "replacements": [
                    {
                        "old": "    return 'world'",
                        "new": "    return 'antigravity'",
                    }
                ],
            }
        ]
    }

    modified = apply_anchor_patch(tmp_path, payload)
    assert len(modified) == 1
    assert target_file.read_text(encoding="utf-8") == "def hello():\n    return 'antigravity'\n"


def test_apply_anchor_patch_sha256_mismatch(tmp_path):
    from ccba_harness.peer import apply_anchor_patch

    target_file = tmp_path / "sample.py"
    target_file.write_text("def hello(): pass\n", encoding="utf-8")

    payload = {
        "files": [
            {
                "path": "sample.py",
                "blob_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "replacements": [{"old": "pass", "new": "return 1"}],
            }
        ]
    }

    with pytest.raises(ValueError, match="Anchor patch SHA-256 mismatch"):
        apply_anchor_patch(tmp_path, payload)


def test_apply_anchor_patch_duplicate_old_string(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    target_file = tmp_path / "sample.py"
    content = "item = 1\nitem = 1\n"
    target_file.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "sample.py",
                "blob_sha256": sha,
                "replacements": [{"old": "item = 1", "new": "item = 2"}],
            }
        ]
    }

    with pytest.raises(ValueError, match="Target old anchor text is not unique"):
        apply_anchor_patch(tmp_path, payload)


def test_apply_anchor_patch_path_traversal_prevention(tmp_path):
    from ccba_harness.peer import apply_anchor_patch

    payload = {
        "files": [
            {
                "path": "../../etc/passwd",
                "blob_sha256": "abcdef",
                "replacements": [{"old": "root", "new": "hacked"}],
            }
        ]
    }
    with pytest.raises(ValueError, match="Path traversal detected in patch"):
        apply_anchor_patch(tmp_path, payload)


def test_invoke_grok_cli_profile_and_tier_resolution(tmp_path, monkeypatch):
    from ccba_harness.peer import invoke_grok_cli

    prompt = tmp_path / "prompt.md"
    envelope = PeerPromptEnvelope(
        request_id="req-tier-test",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Tier Resolution Test",
        timestamp="2026-10-05T15:00:00+07:00",
        output_path="resp.md",
        profile="patch_fast",
    )
    prompt.write_text(render_prompt_header(envelope) + "Body", encoding="utf-8")

    captured_cmds = []

    def mock_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        verdict = PeerVerdictBlock(
            request_id="req-tier-test",
            verdict="GATE_PASS",
            summary="Pass",
        )
        import subprocess

        return subprocess.CompletedProcess(
            cmd, returncode=0, stdout=render_verdict_header(verdict) + "OK", stderr=""
        )

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_run)

    # 1. Profile patch_fast defaults to model qwen-local and max_turns=1
    ok = invoke_grok_cli(prompt, profile="patch_fast")
    assert ok is True
    assert "-m" in captured_cmds[0]
    assert captured_cmds[0][captured_cmds[0].index("-m") + 1] == "qwen-local"
    assert "--max-turns" in captured_cmds[0]
    assert captured_cmds[0][captured_cmds[0].index("--max-turns") + 1] == "1"

    # 2. Tier 'gateway' maps to gemini-38-flash
    ok = invoke_grok_cli(prompt, tier="gateway")
    assert ok is True
    assert captured_cmds[1][captured_cmds[1].index("-m") + 1] == "gemini-38-flash"
