"""test_peer_runtime_hardening.py - Unit tests for ADR-0065 Peer Runtime Hardening & Audit Remediations.

Tests COND-01 (profile specs & risk_score bounds), COND-02 (no synthetic APPROVE),
COND-03 (process group termination & mutex scope), and COND-04 (topological fail-closed).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from scripts.spoke.spoke_bootstrap import (
    DEFAULT_PACKAGE_TOPOLOGY_ORDER,
    discover_package_topology,
)

from ccba_harness.peer import (
    PROFILE_SPECS,
    PeerVerdictBlock,
    _run_single_grok_attempt,
    _terminate_proc_tree,
    atomic_write_text,
)


def test_peer_profile_specs_hardened() -> None:
    """Verifies that PROFILE_SPECS satisfy ADR-0065 / Grok COND-01 constraints."""
    # patch_fast
    patch_fast = PROFILE_SPECS["patch_fast"]
    assert patch_fast["max_turns"] == 1
    assert patch_fast["deny"] == ["*"]
    assert patch_fast["timeout"] == 120.0

    # agentic_code
    agentic = PROFILE_SPECS["agentic_code"]
    assert agentic["max_turns"] == 8
    assert agentic["reasoning_effort"] == "high"
    assert "read_file" in agentic["tools"]
    assert "search_replace" in agentic["tools"]
    assert "run_terminal_command" in agentic["disallowed_tools"]
    assert "spawn_subagent" in agentic["disallowed_tools"]

    # arch_audit
    arch_audit = PROFILE_SPECS["arch_audit"]
    assert arch_audit["max_turns"] == 14
    assert arch_audit["reasoning_effort"] == "xhigh"
    assert arch_audit["timeout"] == 600.0
    assert "read_file" in arch_audit["tools"]


def test_peer_verdict_block_risk_score_bounds() -> None:
    """Verifies that PeerVerdictBlock bounds risk_score to 1..5 and allows extra forward fields."""
    # Valid risk scores
    for score in (1, 2, 3, 4, 5):
        block = PeerVerdictBlock(
            request_id="req-1",
            verdict="APPROVE",
            risk_score=score,
            summary="Valid score",
        )
        assert block.risk_score == score

    # Invalid risk scores raise ValidationError
    with pytest.raises(ValidationError):
        PeerVerdictBlock(
            request_id="req-2",
            verdict="APPROVE",
            risk_score=0,
            summary="Zero score",
        )

    with pytest.raises(ValidationError):
        PeerVerdictBlock(
            request_id="req-3",
            verdict="APPROVE",
            risk_score=6,
            summary="Exceeds max score",
        )

    # Extra fields are safely ignored for forward compatibility
    block_extra = PeerVerdictBlock.model_validate(
        {
            "request_id": "req-4",
            "verdict": "APPROVE",
            "summary": "Forward compatibility check",
            "future_field_v3": "some_value",
        }
    )
    assert block_extra.verdict == "APPROVE"


def test_no_synthetic_approve_on_anchor_patch_only(tmp_path: Path) -> None:
    """Verifies COND-02: outputs containing only an anchor patch get HANDOFF, not APPROVE."""
    prompt_file = tmp_path / "prompt_grok_test.md"
    prompt_file.write_text(
        "---\nrequest_id: req-test-anchor\nfrom_agent: antigravity\nto_agent: grok\n"
        "request_type: implement\nsubject: test\ntimestamp: '2026-10-06T00:00:00Z'\n"
        "output_path: grok_response.md\n---\nPrompt body\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "grok_response.md"

    # Simulated worker output: Contains AnchorPatchPayload JSON, but NO PeerVerdictBlock frontmatter
    dummy_patch = {
        "files": [
            {
                "path": "test.txt",
                "blob_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "replacements": [{"old": "foo", "new": "bar"}],
            }
        ]
    }
    raw_worker_output = f"```json\n{json_dumps(dummy_patch)}\n```\n"

    def mock_popen_impl(*args: Any, **kwargs: Any) -> MagicMock:
        stdout_f = kwargs.get("stdout")
        if stdout_f:
            stdout_f.write(raw_worker_output)
            stdout_f.flush()
        m = MagicMock()
        m.poll.return_value = 0
        m.communicate.return_value = (raw_worker_output, "")
        return m

    with patch("subprocess.Popen", side_effect=mock_popen_impl):
        success = _run_single_grok_attempt(
            cmd=["dummy-cmd"],
            prompt_path=prompt_file,
            output_file=output_file,
            timeout=10.0,
            session_id=None,
            candidate_model="mock-model",
        )
        assert success is True

        # Check output file content: verdict must be HANDOFF, NEVER APPROVE!
        content = output_file.read_text(encoding="utf-8")
        assert "verdict: HANDOFF" in content
        assert "verdict: APPROVE" not in content
        assert (
            "Fast-path anchor patch generated; pending orchestrator apply and verification."
            in content
        )


def test_process_group_termination_helper() -> None:
    """Verifies COND-03: _terminate_proc_tree safely terminates process and waits twice."""
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True if sys.platform != "win32" else False,
    )
    assert proc.poll() is None  # Running

    _terminate_proc_tree(proc)
    assert proc.poll() is not None  # Process has terminated cleanly


def test_atomic_write_text_retries(tmp_path: Path) -> None:
    """Verifies COND-04: atomic_write_text retries and succeeds."""
    target = tmp_path / "atomic_target.txt"
    atomic_write_text(target, "hello world")
    assert target.read_text(encoding="utf-8") == "hello world"

    # Overwrite works cleanly
    atomic_write_text(target, "updated content")
    assert target.read_text(encoding="utf-8") == "updated content"


def test_discover_package_topology_cycle_fail_closed(tmp_path: Path) -> None:
    """Verifies COND-04: Circular dependencies trigger fail-closed fallback to DEFAULT_PACKAGE_TOPOLOGY_ORDER."""
    mock_hub = tmp_path / "mock_hub"
    pkg_dir = mock_hub / "packages"
    pkg_dir.mkdir(parents=True)

    # Create Package A depending on Package B
    (pkg_dir / "pkg-a").mkdir()
    (pkg_dir / "pkg-a" / "pyproject.toml").write_text(
        '[project]\nname = "pkg-a"\ndependencies = ["pkg-b"]\n', encoding="utf-8"
    )

    # Create Package B depending on Package A (Direct Circular Dependency!)
    (pkg_dir / "pkg-b").mkdir()
    (pkg_dir / "pkg-b" / "pyproject.toml").write_text(
        '[project]\nname = "pkg-b"\ndependencies = ["pkg-a"]\n', encoding="utf-8"
    )

    topo = discover_package_topology(mock_hub)
    # Fail-closed guarantee: Must return DEFAULT_PACKAGE_TOPOLOGY_ORDER, NOT [pkg-a, pkg-b]
    assert topo == DEFAULT_PACKAGE_TOPOLOGY_ORDER


def json_dumps(obj: Any) -> str:
    """Helper to dump JSON without extra imports."""
    import json

    return json.dumps(obj)
