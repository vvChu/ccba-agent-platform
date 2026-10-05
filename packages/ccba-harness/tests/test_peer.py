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

    class MockPopen:
        def __init__(self, cmd, **kwargs):
            if not (len(cmd) > 1 and cmd[1] == "usage"):
                captured_cmds.append(cmd)
            verdict = PeerVerdictBlock(
                request_id="req-auto-1",
                verdict="APPROVE",
                summary="Auto-grok test passed.",
            )
            self._stdout = render_verdict_header(verdict) + "Review complete."
            self.returncode = 0
            self.pid = 12345

        def poll(self):
            return 0

        def communicate(self, timeout=None):
            return self._stdout, ""

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", MockPopen)
    success = invoke_grok_cli(prompt_file, model="gemini-38-flash")
    assert success is True
    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    assert "--always-approve" in cmd
    assert "--no-subagents" in cmd
    assert "--reasoning-effort" in cmd
    assert "xhigh" in cmd
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

    class MockPopenAsync:
        def __init__(self, cmd, **kwargs):
            verdict = PeerVerdictBlock(
                request_id="req-live-auto",
                verdict="APPROVE",
                summary="Async auto-grok completed successfully.",
            )
            self._stdout = render_verdict_header(verdict) + "Async review content."
            self.returncode = 0
            self.pid = 54321

        def poll(self):
            return 0

        def communicate(self, timeout=None):
            return self._stdout, ""

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", MockPopenAsync)

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


def test_watchdog_ignores_stale_pre_existing_output_file(tmp_path, monkeypatch):
    import os
    import time

    from ccba_harness.peer import safe_read_and_hash

    envelope = PeerPromptEnvelope(
        request_id="req-fresh",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Stale File Watchdog Test",
        timestamp="2026-10-05T20:00:00+07:00",
        output_path="grok_stale_test.md",
    )
    prompt_file = tmp_path / "prompt_stale.md"
    atomic_write_text(prompt_file, render_prompt_header(envelope) + "Check fresh.")

    out_file = tmp_path / "grok_stale_test.md"
    stale_verdict = PeerVerdictBlock(
        request_id="req-stale-old",
        verdict="REVISE_PLAN",
        summary="Old stale verdict.",
    )
    atomic_write_text(out_file, render_verdict_header(stale_verdict) + "Old content.")
    old_time = time.time() - 3600
    os.utime(out_file, (old_time, old_time))

    class MockPopenFresh:
        def __init__(self, cmd, **kwargs):
            fresh_verdict = PeerVerdictBlock(
                request_id="req-fresh",
                verdict="APPROVE",
                summary="Fresh run verdict.",
            )
            self._stdout = render_verdict_header(fresh_verdict) + "Fresh content."
            self.returncode = 0
            self.pid = 77777

        def poll(self):
            return 0

        def communicate(self, timeout=None):
            return self._stdout, ""

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", MockPopenFresh)

    ok = invoke_grok_cli(prompt_file, model="gemini-38-flash")
    assert ok is True
    fresh_content, _ = safe_read_and_hash(out_file)
    parsed = parse_verdict_from_md(fresh_content)
    assert parsed is not None
    assert parsed.request_id == "req-fresh"
    assert parsed.verdict == "APPROVE"


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
        "--output-format",
        "plain",
        "--worktree",
        "--prompt-file",
        str(prompt),
    ]

    cmd_with_sys = build_grok_cmd(
        prompt_path=prompt,
        model="qwen-local",
        system_prompt="Custom system prompt override",
        deny=["*"],
    )
    assert "--system-prompt-override" in cmd_with_sys
    idx = cmd_with_sys.index("--system-prompt-override")
    assert cmd_with_sys[idx + 1] == "Custom system prompt override"
    assert "--deny" in cmd_with_sys
    deny_idx = cmd_with_sys.index("--deny")
    assert cmd_with_sys[deny_idx + 1] == "*"


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


def test_apply_anchor_patch_multi_file_atomicity(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("var1 = 10\n", encoding="utf-8")
    file2.write_text("var2 = 20\n", encoding="utf-8")
    sha1 = hashlib.sha256(b"var1 = 10\n").hexdigest()

    # file 1 is valid, but file 2 has sha mismatch
    payload = {
        "files": [
            {
                "path": "file1.py",
                "blob_sha256": sha1,
                "replacements": [{"old": "var1 = 10", "new": "var1 = 99"}],
            },
            {
                "path": "file2.py",
                "blob_sha256": "wrong_sha256_hash_value_here",
                "replacements": [{"old": "var2 = 20", "new": "var2 = 99"}],
            },
        ]
    }

    with pytest.raises(ValueError, match="Anchor patch SHA-256 mismatch"):
        apply_anchor_patch(tmp_path, payload)

    # Invariant: file1 must remain unchanged because file2 failed in Phase 1
    assert file1.read_text(encoding="utf-8") == "var1 = 10\n"


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

    class MockPopenTier:
        def __init__(self, cmd, **kwargs):
            if not (len(cmd) > 1 and cmd[1] == "usage"):
                captured_cmds.append(cmd)
            verdict = PeerVerdictBlock(
                request_id="req-tier-test",
                verdict="GATE_PASS",
                summary="Pass",
            )
            self._stdout = render_verdict_header(verdict) + "OK"
            self.returncode = 0
            self.pid = 999

        def poll(self):
            return 0

        def communicate(self, timeout=None):
            return self._stdout, ""

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", MockPopenTier)

    # 1. Profile patch_fast defaults to model qwen-local and deny *
    ok = invoke_grok_cli(prompt, profile="patch_fast")
    assert ok is True
    assert "-m" in captured_cmds[0]
    assert captured_cmds[0][captured_cmds[0].index("-m") + 1] == "qwen-local"
    assert "--deny" in captured_cmds[0]
    assert captured_cmds[0][captured_cmds[0].index("--deny") + 1] == "*"

    # 2. Tier 'gateway' maps to gemini-38-flash
    ok = invoke_grok_cli(prompt, tier="gateway")
    assert ok is True
    assert captured_cmds[1][captured_cmds[1].index("-m") + 1] == "gemini-38-flash"


def test_extract_anchor_payload():
    from ccba_harness.peer import extract_anchor_payload

    # Valid payload in markdown code block
    md = """Here is the patch:
```json
{
  "files": [
    {
      "path": "src/foo.py",
      "blob_sha256": "abcdef123456",
      "replacements": [{"old": "x", "new": "y"}]
    }
  ]
}
```
"""
    payload = extract_anchor_payload(md)
    assert payload is not None
    assert len(payload.files) == 1
    assert payload.files[0].path == "src/foo.py"

    # Invalid / empty
    assert extract_anchor_payload("") is None
    assert extract_anchor_payload("not json") is None


def test_extract_frontmatter_with_markdown_code_fence():
    md = """```markdown
---
request_id: test-fence-001
verdict: APPROVE
summary: "Wrapped frontmatter"
---
Body text here.
```
"""
    fm, body = extract_frontmatter(md)
    assert fm is not None
    assert fm["request_id"] == "test-fence-001"
    assert fm["verdict"] == "APPROVE"
    assert "Body text here." in body


def test_apply_anchor_patch_dry_run(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    f = tmp_path / "target.py"
    content = "x = 1\ny = 2\n"
    f.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "target.py",
                "blob_sha256": sha,
                "replacements": [{"old": "x = 1", "new": "x = 99"}],
            }
        ]
    }

    # dry_run returns modified paths but does not touch disk
    modified = apply_anchor_patch(tmp_path, payload, dry_run=True)
    assert len(modified) == 1
    assert modified[0] == f
    assert f.read_text(encoding="utf-8") == content  # unchanged on disk


def test_apply_anchor_patch_duplicate_target_file(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    f = tmp_path / "target.py"
    content = "x = 1\ny = 2\n"
    f.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "target.py",
                "blob_sha256": sha,
                "replacements": [{"old": "x = 1", "new": "x = 10"}],
            },
            {
                "path": "target.py",
                "blob_sha256": sha,
                "replacements": [{"old": "y = 2", "new": "y = 20"}],
            },
        ]
    }

    with pytest.raises(ValueError, match="duplicate target file"):
        apply_anchor_patch(tmp_path, payload)


def test_apply_anchor_patch_crlf_normalization(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    f = tmp_path / "crlf_file.py"
    # Write file with CRLF
    content = "def hello():\r\n    return 'world'\r\n"
    f.write_bytes(content.encode("utf-8"))
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Replacement payload with LF
    payload = {
        "files": [
            {
                "path": "crlf_file.py",
                "blob_sha256": sha,
                "replacements": [
                    {
                        "old": "def hello():\n    return 'world'",
                        "new": "def hello():\n    return 'vietnam'",
                    }
                ],
            }
        ]
    }

    apply_anchor_patch(tmp_path, payload)
    new_content = f.read_text(encoding="utf-8")
    assert "vietnam" in new_content


def test_apply_anchor_patch_transactional_rollback(tmp_path, monkeypatch):
    import hashlib

    import ccba_harness.peer
    from ccba_harness.peer import apply_anchor_patch

    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"

    c1 = "alpha = 10\n"
    c2 = "beta = 20\n"
    f1.write_text(c1, encoding="utf-8")
    f2.write_text(c2, encoding="utf-8")

    sha1 = hashlib.sha256(c1.encode("utf-8")).hexdigest()
    sha2 = hashlib.sha256(c2.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "file1.txt",
                "blob_sha256": sha1,
                "replacements": [{"old": "alpha = 10", "new": "alpha = 999"}],
            },
            {
                "path": "file2.txt",
                "blob_sha256": sha2,
                "replacements": [{"old": "beta = 20", "new": "beta = 888"}],
            },
        ]
    }

    original_atomic_write = ccba_harness.peer.atomic_write_text

    def mock_atomic_write(path, text):
        if str(path).endswith("file2.txt"):
            raise OSError("Disk write failed unexpectedly on file2")
        return original_atomic_write(path, text)

    monkeypatch.setattr(ccba_harness.peer, "atomic_write_text", mock_atomic_write)

    with pytest.raises(ValueError, match="Transaction aborted during write phase"):
        apply_anchor_patch(tmp_path, payload)

    # Rollback must restore file1 to original content
    assert f1.read_text(encoding="utf-8") == c1
    assert f2.read_text(encoding="utf-8") == c2


def test_apply_anchor_patch_backup(tmp_path):
    import hashlib

    from ccba_harness.peer import apply_anchor_patch

    f = tmp_path / "config.ini"
    content = "mode = test\n"
    f.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    payload = {
        "files": [
            {
                "path": "config.ini",
                "blob_sha256": sha,
                "replacements": [{"old": "mode = test", "new": "mode = prod"}],
            }
        ]
    }

    apply_anchor_patch(tmp_path, payload, backup=True)
    assert f.read_text(encoding="utf-8") == "mode = prod\n"

    bak = tmp_path / "config.ini.bak"
    assert bak.exists()
    assert bak.read_text(encoding="utf-8") == content


def test_run_apply_anchor_patch_cli_flows(tmp_path, capsys, monkeypatch):
    import hashlib
    import io
    import json

    from ccba_harness.cli import run_apply_anchor_patch_cli

    f = tmp_path / "app.py"
    content = "status = 'starting'\n"
    f.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    patch_dict = {
        "files": [
            {
                "path": "app.py",
                "blob_sha256": sha,
                "replacements": [{"old": "status = 'starting'", "new": "status = 'running'"}],
            }
        ]
    }
    patch_file = tmp_path / "patch.json"
    patch_file.write_text(json.dumps(patch_dict), encoding="utf-8")

    # 1. Test dry-run with json output
    exit_code = run_apply_anchor_patch_cli(
        [
            "--patch-file",
            str(patch_file),
            "--root",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "DRY_RUN_OK"
    assert res["files"] == ["app.py"]
    assert f.read_text(encoding="utf-8") == content  # unchanged

    # 2. Test apply with backup and quiet
    exit_code = run_apply_anchor_patch_cli(
        [
            "-f",
            str(patch_file),
            "-r",
            str(tmp_path),
            "--backup",
            "-q",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""  # quiet mode
    assert f.read_text(encoding="utf-8") == "status = 'running'\n"
    assert (tmp_path / "app.py.bak").exists()

    # 3. Test reading from stdin (-)
    f2 = tmp_path / "server.py"
    c2 = "port = 8080\n"
    f2.write_text(c2, encoding="utf-8")
    sha2 = hashlib.sha256(c2.encode("utf-8")).hexdigest()
    stdin_patch = json.dumps(
        {
            "files": [
                {
                    "path": "server.py",
                    "blob_sha256": sha2,
                    "replacements": [{"old": "port = 8080", "new": "port = 9090"}],
                }
            ]
        }
    )

    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_patch))
    exit_code = run_apply_anchor_patch_cli(
        [
            "-f",
            "-",
            "-r",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert f2.read_text(encoding="utf-8") == "port = 9090\n"
    capsys.readouterr()

    # 4. Error path: file not found
    exit_code = run_apply_anchor_patch_cli(["-f", "non_existent.json", "--json"])
    assert exit_code == 1
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "ERROR"


def test_new_peer_profiles_specs():
    from ccba_harness.peer import PROFILE_SPECS

    assert "code_review" in PROFILE_SPECS
    cr = PROFILE_SPECS["code_review"]
    assert cr["max_turns"] == 10
    assert cr["reasoning_effort"] == "high"
    assert "write_file" in cr["disallowed_tools"]
    assert "read_file" in cr["tools"]

    assert "arch_audit" in PROFILE_SPECS
    aa = PROFILE_SPECS["arch_audit"]
    assert aa["max_turns"] == 8
    assert aa["reasoning_effort"] == "xhigh"
    assert "write_file" in aa["disallowed_tools"]


def test_parse_verdict_with_string_conditions_and_extra_fields():
    md = """---
request_id: "req-test-conds-001"
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - "Condition string item 1"
  - "Condition string item 2"
findings_count:
  critical: 0
  major: 1
reviewer: "grok"
summary: "Approved with string conditions"
---
Review body text.
"""
    vb = parse_verdict_from_md(md)
    assert vb is not None
    assert vb.verdict == "APPROVE_WITH_CONDITIONS"
    assert len(vb.conditions) == 2
    assert vb.conditions[0].id == "COND-01"
    assert vb.conditions[0].description == "Condition string item 1"
    assert vb.conditions[1].id == "COND-02"
    assert vb.conditions[1].description == "Condition string item 2"
    assert vb.summary == "Approved with string conditions"


def test_apply_anchor_patch_directory_rejection(tmp_path):
    from ccba_harness.peer import apply_anchor_patch

    sub_dir = tmp_path / "somedir"
    sub_dir.mkdir()

    payload = {
        "files": [
            {
                "path": "somedir",
                "blob_sha256": "dummy",
                "replacements": [],
            }
        ]
    }
    with pytest.raises(ValueError, match="Target patch path is not a regular file"):
        apply_anchor_patch(tmp_path, payload)


def test_atomic_write_text_preserves_executable_mode(tmp_path):
    from ccba_harness.peer import atomic_write_text

    script_file = tmp_path / "script.sh"
    script_file.write_text("#!/bin/bash\necho 1", encoding="utf-8")
    script_file.chmod(0o755)

    atomic_write_text(script_file, "#!/bin/bash\necho 2")
    current_mode = script_file.stat().st_mode & 0o777
    assert current_mode == 0o755
    assert script_file.read_text(encoding="utf-8") == "#!/bin/bash\necho 2"


def test_apply_anchor_patch_rollback_errors_collected(tmp_path, monkeypatch):
    import hashlib

    import ccba_harness.peer as peer_mod
    from ccba_harness.peer import apply_anchor_patch

    file1 = tmp_path / "f1.txt"
    file2 = tmp_path / "f2.txt"
    file1.write_text("file1 initial", encoding="utf-8")
    file2.write_text("file2 initial", encoding="utf-8")

    payload = {
        "files": [
            {
                "path": "f1.txt",
                "blob_sha256": hashlib.sha256(b"file1 initial").hexdigest(),
                "replacements": [{"old": "initial", "new": "updated"}],
            },
            {
                "path": "f2.txt",
                "blob_sha256": hashlib.sha256(b"file2 initial").hexdigest(),
                "replacements": [{"old": "initial", "new": "updated"}],
            },
        ]
    }

    real_atomic_write = peer_mod.atomic_write_text
    call_count = 0

    def mock_atomic_write(target, content):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            # Fail writing file 2 during forward commit
            raise OSError("Simulated disk error on forward write")
        if call_count == 3:
            # Fail during rollback of file 1
            raise OSError("Simulated disk error on rollback")
        return real_atomic_write(target, content)

    monkeypatch.setattr(peer_mod, "atomic_write_text", mock_atomic_write)

    with pytest.raises(
        ValueError, match=r"Rollback errors: f1\.txt: Simulated disk error on rollback"
    ):
        apply_anchor_patch(tmp_path, payload)
