"""Unit tests for Multi-Agent Co-Review Orchestration & Consensus Engine (ADR-0065)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import get_args
from unittest.mock import patch

import pytest

from ccba_harness.cli import run_peer_co_review_cli
from ccba_harness.peer import (
    VERDICT_LATTICE_RANK,
    PeerCondition,
    PeerPromptEnvelope,
    PeerVerdictBlock,
    PeerVerdictTelemetry,
    VerdictType,
    orchestrate_peer_co_review,
    render_consensus_report_markdown,
    render_prompt_header,
    render_verdict_header,
    synthesize_verdicts,
)


def test_verdict_lattice_coverage_and_invariants() -> None:
    """Verifies that VERDICT_LATTICE_RANK strictly covers 100% of VerdictType tokens (COND-01)."""
    expected_verdicts = set(get_args(VerdictType))
    lattice_keys = set(VERDICT_LATTICE_RANK.keys())
    assert lattice_keys == expected_verdicts, (
        f"Lattice missing items: {expected_verdicts - lattice_keys}"
    )

    # Blocker tokens must have higher rank than revision/handoff/conditional/pass
    assert VERDICT_LATTICE_RANK["REJECT"] > VERDICT_LATTICE_RANK["REVISE_PLAN"]
    assert VERDICT_LATTICE_RANK["REVISE_PLAN"] > VERDICT_LATTICE_RANK["HANDOFF"]
    assert VERDICT_LATTICE_RANK["HANDOFF"] > VERDICT_LATTICE_RANK["APPROVE_WITH_CONDITIONS"]
    assert VERDICT_LATTICE_RANK["APPROVE_WITH_CONDITIONS"] > VERDICT_LATTICE_RANK["APPROVE"]


def test_synthesize_verdicts_unanimous() -> None:
    """Unanimous consensus across all completed agents must retain the exact token (COND-01)."""
    verdicts = {
        "code_review": PeerVerdictBlock(
            request_id="req-1",
            verdict="APPROVE_PLAN",
            summary="Code plan looks good.",
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-1",
            verdict="APPROVE_PLAN",
            summary="Architecture plan adheres to ADR-0065.",
        ),
    }
    report = synthesize_verdicts(request_id="req-1", verdicts=verdicts)
    assert report.verdict == "APPROVE_PLAN"
    assert report.risk_score == 1
    assert report.failed_profiles == []


def test_synthesize_verdicts_precedence_lattice() -> None:
    """Verifies strict lattice precedence when differing verdicts are issued (COND-01)."""
    # 1. REJECT dominates APPROVE
    v_reject = {
        "code_review": PeerVerdictBlock(
            request_id="req-2",
            verdict="REJECT",
            summary="Fatal memory leak found.",
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-2",
            verdict="APPROVE",
            summary="Architecture is fine.",
        ),
    }
    assert synthesize_verdicts("req-2", v_reject).verdict == "REJECT"

    # 2. REJECT_PLAN dominates APPROVE_WITH_CONDITIONS
    v_reject_plan = {
        "code_review": PeerVerdictBlock(
            request_id="req-2",
            verdict="APPROVE_WITH_CONDITIONS",
            summary="Small style issue.",
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-2",
            verdict="REJECT_PLAN",
            summary="Plan violates monorepo isolation.",
        ),
    }
    assert synthesize_verdicts("req-2", v_reject_plan).verdict == "REJECT_PLAN"

    # 3. REVISE_PLAN dominates APPROVE
    v_revise = {
        "code_review": PeerVerdictBlock(
            request_id="req-2",
            verdict="REVISE_PLAN",
            summary="Need more unit test cases.",
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-2",
            verdict="APPROVE",
            summary="Looks okay.",
        ),
    }
    assert synthesize_verdicts("req-2", v_revise).verdict == "REVISE_PLAN"


def test_synthesize_verdicts_escalation_by_blocking_condition_or_risk() -> None:
    """PASS verdict is escalated to APPROVE_WITH_CONDITIONS if blocking conditions or risk >= 4 exist (COND-01)."""
    # Case A: APPROVE with blocking=True condition -> escalated
    v_with_blocking = {
        "code_review": PeerVerdictBlock(
            request_id="req-3",
            verdict="APPROVE",
            conditions=[
                PeerCondition(id="COND-01", description="Missing index check", blocking=True)
            ],
            summary="Passed with required fix.",
        ),
    }
    rep_a = synthesize_verdicts("req-3", v_with_blocking)
    assert rep_a.verdict == "APPROVE_WITH_CONDITIONS"

    # Case B: APPROVE with advisory-only (blocking=False) condition -> stays APPROVE
    v_advisory_only = {
        "code_review": PeerVerdictBlock(
            request_id="req-3",
            verdict="APPROVE",
            conditions=[
                PeerCondition(id="COND-01", description="Consider renaming var", blocking=False)
            ],
            summary="Clean pass.",
        ),
    }
    rep_b = synthesize_verdicts("req-3", v_advisory_only)
    assert rep_b.verdict == "APPROVE"

    # Case C: APPROVE with risk_score >= 4 -> escalated to APPROVE_WITH_CONDITIONS
    v_high_risk = {
        "code_review": PeerVerdictBlock(
            request_id="req-3",
            verdict="APPROVE",
            risk_score=4,
            summary="High blast radius.",
        ),
    }
    rep_c = synthesize_verdicts("req-3", v_high_risk)
    assert rep_c.verdict == "APPROVE_WITH_CONDITIONS"
    assert rep_c.risk_score == 4


def test_synthesize_verdicts_condition_deduplication_and_or_merge() -> None:
    """Verifies that duplicated condition descriptions merge blocking with OR and record source profiles (COND-03)."""
    v_merge = {
        "code_review": PeerVerdictBlock(
            request_id="req-4",
            verdict="APPROVE",
            conditions=[
                PeerCondition(id="C-1", description="Add validation check", blocking=False),
            ],
            summary="Review 1",
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-4",
            verdict="APPROVE",
            conditions=[
                PeerCondition(id="C-2", description="Add validation check", blocking=True),
                PeerCondition(id="C-3", description="Update ADR documentation", blocking=True),
            ],
            summary="Review 2",
        ),
    }
    rep = synthesize_verdicts("req-4", v_merge, expected_profiles=["code_review", "arch_audit"])
    assert len(rep.conditions) == 2

    # The duplicated condition should now have blocking=True (False OR True)
    c_val = next(c for c in rep.conditions if "validation check" in c.description.lower())
    assert c_val.blocking is True
    assert set(c_val.source_profiles) == {"code_review", "arch_audit"}

    c_adr = next(c for c in rep.conditions if "adr documentation" in c.description.lower())
    assert c_adr.blocking is True
    assert c_adr.source_profiles == ["arch_audit"]


def test_synthesize_verdicts_quorum_failure_handoff() -> None:
    """Missing or failed expected profile results in HANDOFF with failure condition (COND-02)."""
    v_partial = {
        "code_review": PeerVerdictBlock(
            request_id="req-5",
            verdict="APPROVE",
            summary="Code is clean.",
        ),
    }
    rep = synthesize_verdicts(
        "req-5",
        verdicts=v_partial,
        expected_profiles=["code_review", "arch_audit"],
    )
    assert rep.verdict == "HANDOFF"
    assert rep.completed_profiles == ["code_review"]
    assert rep.failed_profiles == ["arch_audit"]
    assert any("arch_audit" in c.description for c in rep.conditions)

    # However, if completed profile was a BLOCKER, the blocker wins over HANDOFF
    v_partial_blocker = {
        "code_review": PeerVerdictBlock(
            request_id="req-5",
            verdict="REJECT",
            summary="Fatal issue.",
        ),
    }
    rep_block = synthesize_verdicts(
        "req-5",
        verdicts=v_partial_blocker,
        expected_profiles=["code_review", "arch_audit"],
    )
    assert rep_block.verdict == "REJECT"
    assert rep_block.failed_profiles == ["arch_audit"]


def test_synthesize_verdicts_telemetry_aggregation() -> None:
    """Verifies aggregation of tokens, costs, durations, and profile breakdowns (COND-05)."""
    tel_a = PeerVerdictTelemetry(
        session_id="sess-a",
        primary_model="gemini-38-flash",
        input_tokens=1000,
        output_tokens=200,
        reasoning_tokens=50,
        total_tokens=1200,
        cost_usd=0.0125,
        cost_mode="exact",
        duration_seconds=15.0,
    )
    tel_b = PeerVerdictTelemetry(
        session_id="sess-b",
        primary_model="grok-4.7",
        input_tokens=5000,
        output_tokens=800,
        reasoning_tokens=300,
        total_tokens=5800,
        cost_usd=0.0850,
        cost_mode="exact",
        duration_seconds=30.0,
    )
    v_map = {
        "code_review": PeerVerdictBlock(
            request_id="req-6",
            verdict="APPROVE",
            summary="Pass",
            telemetry=tel_a,
        ),
        "arch_audit": PeerVerdictBlock(
            request_id="req-6",
            verdict="APPROVE",
            summary="Pass",
            telemetry=tel_b,
        ),
    }
    rep = synthesize_verdicts("req-6", v_map, duration_seconds=32.5)
    assert rep.combined_telemetry is not None
    ct = rep.combined_telemetry
    assert ct.total_tokens == 7000
    assert ct.input_tokens == 6000
    assert ct.output_tokens == 1000
    assert ct.reasoning_tokens == 350
    assert ct.cost_usd == pytest.approx(0.0975, abs=1e-4)
    assert ct.wall_seconds == 32.5
    assert ct.sum_agent_seconds == 45.0
    assert ct.cost_mode == "exact"
    assert "code_review" in ct.profile_breakdown
    assert "arch_audit" in ct.profile_breakdown


def test_orchestrate_peer_co_review_tempdir_isolation() -> None:
    """Ensures intermediate prompt copies and partial verdicts are never leaked to prompt directory (COND-04)."""
    with tempfile.TemporaryDirectory() as td:
        prompt_dir = Path(td)
        prompt_file = prompt_dir / "prompt_feature.md"
        output_file = prompt_dir / "grok_consensus_final.md"

        envelope = PeerPromptEnvelope(
            request_id="req-test-iso",
            from_agent="antigravity",
            to_agent="grok",
            request_type="review",
            subject="Test Isolation Review",
            timestamp="2026-10-06T07:00:00Z",
            output_path="grok_feature.md",
        )
        prompt_file.write_text(render_prompt_header(envelope) + "# Prompt Body", encoding="utf-8")

        # Mock invoke_grok_cli to simulate successful writing of individual verdict files in tempdir
        def _mock_invoke(prompt_path: Path, **kwargs) -> bool:
            out_name = f"grok_{kwargs.get('profile', 'unknown')}.md"
            out_path = prompt_path.parent / out_name
            vb = PeerVerdictBlock(
                request_id="req-test-iso",
                verdict="APPROVE",
                summary=f"Approved by {kwargs.get('profile')}",
            )
            out_path.write_text(render_verdict_header(vb) + "All good.", encoding="utf-8")
            return True

        with patch("ccba_harness.peer.invoke_grok_cli", side_effect=_mock_invoke):
            rep = orchestrate_peer_co_review(
                prompt_path=prompt_file,
                profiles=["code_review", "arch_audit"],
                output_file=output_file,
            )

        assert rep is not None
        assert rep.verdict == "APPROVE"
        assert output_file.exists()

        # Check prompt directory: ONLY prompt_file and output_file must exist.
        # No prompt_*.tmp.md or grok_code_review.md should be in prompt_dir!
        files_in_dir = {p.name for p in prompt_dir.iterdir()}
        assert files_in_dir == {"prompt_feature.md", "grok_consensus_final.md"}


def test_run_peer_co_review_cli_dry_run_and_exit_codes() -> None:
    """Verifies CLI behavior on --dry-run and structured exit codes (COND-06)."""
    with tempfile.TemporaryDirectory() as td:
        prompt_file = Path(td) / "prompt_cli.md"
        envelope = PeerPromptEnvelope(
            request_id="req-cli-001",
            from_agent="antigravity",
            to_agent="grok",
            request_type="review",
            subject="Test CLI Review",
            timestamp="2026-10-06T07:00:00Z",
            output_path="grok_out.md",
        )
        prompt_file.write_text(render_prompt_header(envelope) + "# Content", encoding="utf-8")

        # 1. Dry run
        ret_dry = run_peer_co_review_cli(["--prompt-file", str(prompt_file), "--dry-run"])
        assert ret_dry == 0

        # 2. Mock execute returning REJECT -> exit code 4
        mock_rep_reject = synthesize_verdicts(
            "req-cli-001",
            {
                "code_review": PeerVerdictBlock(
                    request_id="req-cli-001", verdict="REJECT", summary="Fail"
                )
            },
        )
        with patch("ccba_harness.peer.orchestrate_peer_co_review", return_value=mock_rep_reject):
            ret_reject = run_peer_co_review_cli(["--prompt-file", str(prompt_file)])
            assert ret_reject == 4

        # 3. Mock execute returning APPROVE_WITH_CONDITIONS -> exit code 2
        mock_rep_cond = synthesize_verdicts(
            "req-cli-001",
            {
                "code_review": PeerVerdictBlock(
                    request_id="req-cli-001",
                    verdict="APPROVE",
                    conditions=[PeerCondition(id="C1", description="test", blocking=True)],
                    summary="Cond",
                )
            },
        )
        with patch("ccba_harness.peer.orchestrate_peer_co_review", return_value=mock_rep_cond):
            ret_cond = run_peer_co_review_cli(["--prompt-file", str(prompt_file)])
            assert ret_cond == 2

        # 4. Mock execute returning HANDOFF -> exit code 5
        mock_rep_handoff = synthesize_verdicts(
            "req-cli-001",
            {
                "code_review": PeerVerdictBlock(
                    request_id="req-cli-001", verdict="HANDOFF", summary="Handoff"
                )
            },
        )
        with patch("ccba_harness.peer.orchestrate_peer_co_review", return_value=mock_rep_handoff):
            ret_handoff = run_peer_co_review_cli(["--prompt-file", str(prompt_file)])
            assert ret_handoff == 5


def test_render_consensus_report_markdown() -> None:
    """Verifies that consensus markdown contains structured frontmatter and formatted body."""
    rep = synthesize_verdicts(
        "req-render-01",
        {
            "code_review": PeerVerdictBlock(
                request_id="req-render-01",
                verdict="APPROVE",
                summary="Clean code.",
            )
        },
    )
    md = render_consensus_report_markdown(rep)
    assert md.startswith("---\n")
    assert "verdict: APPROVE" in md
    assert "- **Consensus Verdict**: `APPROVE`" in md
