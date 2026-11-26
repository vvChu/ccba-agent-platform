"""test_audit_skill_effectiveness.py - Unit tests for Wave 2 Pre/Post A/B & Drift Auditor."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.governance.audit_skill_effectiveness import (
    DEFAULT_PR909_CUTOFF_UTC,
    audit_routing_and_coverage_drift,
    evaluate_skill_effectiveness,
    load_invocation_events,
    main,
    render_markdown_report,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _make_event(
    *,
    conv: str,
    turn: int,
    created_at: str,
    invoked_skill: str | None,
    recommended_commands: list[str] | None = None,
    prompt_char_len: int = 24,
    is_short_confirmation: bool = False,
    planner_steps: int = 3,
    probe_violations: list[str] | None = None,
    workspace_hash: str = "ws00112233445566",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": f"{conv}:{turn}",
        "conversation_id": conv,
        "turn_index": turn,
        "step_index": turn * 2,
        "created_at": created_at,
        "workspace_hash": workspace_hash,
        "invoked_skill": invoked_skill,
        "mentioned_commands": [],
        "recommended_commands": recommended_commands or [],
        "prompt_char_len": prompt_char_len,
        "is_short_confirmation": is_short_confirmation,
        "tool_counts": {},
        "mutating_tool_count": 1 if "SIDE_EFFECT_VIOLATION" in (probe_violations or []) else 0,
        "planner_steps": planner_steps,
        "probe_violations": probe_violations or [],
        "has_error": "UNEXPECTED_TOOL_ERROR" in (probe_violations or []),
    }


def test_pre_post_cohort_ab_confirmed_vs_candidate_heuristics() -> None:
    """Verify UTC cutoff splitting, confirmed probe counts, and <= 2h adoption heuristics."""
    events = [
        # Pre-PR #909: side-effect violation + bare call + next-turn adoption
        _make_event(
            conv="c1",
            turn=1,
            created_at="2026-11-24T10:00:00Z",
            invoked_skill="ccba-ask",
            recommended_commands=["/ccba-grilling"],
            prompt_char_len=9,
            planner_steps=6,
            probe_violations=["SIDE_EFFECT_VIOLATION"],
        ),
        _make_event(
            conv="c1",
            turn=2,
            created_at="2026-11-24T10:02:00Z",
            invoked_skill="ccba-grilling",
        ),
        # Pre-PR #909: cross-session follow-through within 2h (c2 -> c3 in 45m)
        _make_event(
            conv="c2",
            turn=1,
            created_at="2026-11-24T12:00:00Z",
            invoked_skill="ccba-ask",
            recommended_commands=["/ccba-create-pr"],
            planner_steps=4,
        ),
        _make_event(
            conv="c3",
            turn=1,
            created_at="2026-11-24T12:45:00Z",
            invoked_skill="ccba-create-pr",
        ),
        # Post-PR #909: 0 violations, short choice confirmation next turn
        _make_event(
            conv="c4",
            turn=1,
            created_at="2026-11-25T15:00:00Z",
            invoked_skill="ccba-ask",
            recommended_commands=["/ccba-release-feature"],
            planner_steps=2,
        ),
        _make_event(
            conv="c4",
            turn=2,
            created_at="2026-11-25T15:01:00Z",
            invoked_skill=None,
            is_short_confirmation=True,
        ),
        # Undated event must be excluded cleanly
        _make_event(conv="c5", turn=1, created_at="", invoked_skill="ccba-ask"),
    ]

    report = evaluate_skill_effectiveness(
        events,
        skill="ccba-ask",
        cutoff=DEFAULT_PR909_CUTOFF_UTC,
        follow_window_hours=2.0,
        use_git=False,
    )
    assert report["undated_excluded"] == 1
    assert report["pre"]["confirmed"]["invocations"] == 2
    assert report["pre"]["confirmed"]["bare_invocations"] == 1
    assert report["pre"]["confirmed"]["side_effect_violations"] == 1
    assert report["pre"]["confirmed"]["median_planner_steps"] == 5.0
    assert report["pre"]["candidate_heuristic"]["next_turn_adoption"] == 1
    assert report["pre"]["candidate_heuristic"]["cross_session_follow_through"] == 1
    assert report["pre"]["candidate_heuristic"]["effective_rate"] == 1.0

    assert report["post"]["confirmed"]["invocations"] == 1
    assert report["post"]["confirmed"]["side_effect_violations"] == 0
    assert report["post"]["candidate_heuristic"]["choice_confirmation"] == 1
    assert report["post"]["candidate_heuristic"]["effective_rate"] == 1.0

    md = render_markdown_report(report)
    assert "Side-Effect Violations (`confirmed`)" in md
    assert "Candidate Effective Rate" in md


def test_cross_session_beyond_2h_window_not_counted() -> None:
    """Verify cross-session invocation after 2h cutoff is NOT attributed as follow-through."""
    events = [
        _make_event(
            conv="c1",
            turn=1,
            created_at="2026-11-25T15:00:00Z",
            invoked_skill="ccba-ask",
            recommended_commands=["/ccba-grilling"],
        ),
        _make_event(
            conv="c2",
            turn=1,
            created_at="2026-11-25T18:30:00Z",
            invoked_skill="ccba-grilling",
        ),
    ]
    report = evaluate_skill_effectiveness(
        events,
        skill="ccba-ask",
        cutoff=DEFAULT_PR909_CUTOFF_UTC,
        follow_window_hours=2.0,
        use_git=False,
    )
    assert report["post"]["candidate_heuristic"]["cross_session_follow_through"] == 0
    assert report["post"]["candidate_heuristic"]["effective_turns"] == 0


def test_drift_check_detects_missing_router_and_unconfigured_evals(tmp_path: Path) -> None:
    """Verify --drift-check flags Top-10 skills absent from ccba-ask router or UNCONFIGURED."""
    ask_dir = tmp_path / ".agents" / "skills" / "ccba-ask"
    ask_dir.mkdir(parents=True)
    (ask_dir / "SKILL.md").write_text(
        "# Router\nUse /ccba-ask and /ccba-release-feature.\n", encoding="utf-8"
    )
    tc_dir = tmp_path / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    tc_dir.mkdir(parents=True)
    (tc_dir / "eval_ccba_ask.json").write_text("[]", encoding="utf-8")

    cat = tmp_path / "catalog.yaml"
    cat.write_text(
        "skills:\n  - name: ccba-ask\n  - name: ccba-mystery-top-skill\n",
        encoding="utf-8",
    )

    events = [
        _make_event(conv="c1", turn=1, created_at="2026-11-25T10:00:00Z", invoked_skill="ccba-ask"),
        _make_event(
            conv="c2",
            turn=1,
            created_at="2026-11-25T11:00:00Z",
            invoked_skill="ccba-mystery-top-skill",
        ),
        _make_event(
            conv="c3",
            turn=1,
            created_at="2026-11-25T12:00:00Z",
            invoked_skill="ccba-mystery-top-skill",
        ),
    ]
    drift = audit_routing_and_coverage_drift(
        events,
        tmp_path,
        window_days=30,
        top_n=10,
        catalog_path=cat,
    )
    assert drift["drift_detected"] is True
    assert "ccba-mystery-top-skill" in drift["missing_from_router"]
    assert "ccba-mystery-top-skill" in drift["unconfigured_evals"]
    assert "ccba-ask" not in drift["missing_from_router"]
    assert "ccba-ask" not in drift["unconfigured_evals"]
    assert drift["top_skills"][0]["skill"] == "ccba-mystery-top-skill"


def test_load_from_transcript_dir_and_jsonl_ledger(tmp_path: Path) -> None:
    """Verify loading directly from --transcript-dir and from local JSONL ledger."""
    t_path = tmp_path / "brain" / "conv-t1" / ".system_generated" / "logs" / "transcript.jsonl"
    t_path.parent.mkdir(parents=True)
    rows = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "created_at": "2026-11-24T09:00:00Z",
            "content": "<USER_REQUEST>/ccba-ask kiểm tra /plan giúp tôi</USER_REQUEST>",
        },
        {
            "step_index": 2,
            "type": "PLANNER_RESPONSE",
            "created_at": "2026-11-24T09:00:05Z",
            "content": "Chạy `/ccba-grilling`.",
            "tool_calls": [{"name": "write_file", "args": {"Path": "/tmp/implementation_plan.md"}}],
        },
    ]
    t_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    ev_from_transcripts = load_invocation_events(transcript_dir=tmp_path / "brain")
    assert len(ev_from_transcripts) == 1
    assert "SIDE_EFFECT_VIOLATION" in ev_from_transcripts[0]["probe_violations"]

    ledger = tmp_path / "skill_invocations.jsonl"
    ledger.write_text(json.dumps(ev_from_transcripts[0]) + "\n", encoding="utf-8")
    ev_from_ledger = load_invocation_events(ledger_path=ledger)
    assert len(ev_from_ledger) == 1
    assert ev_from_ledger[0]["event_id"] == ev_from_transcripts[0]["event_id"]


def test_invalid_cutoff_raises_value_error() -> None:
    """Verify naive or malformed cutoff timestamps fail fast with ValueError."""
    with pytest.raises(ValueError, match="Invalid timezone-aware ISO cutoff"):
        evaluate_skill_effectiveness([], cutoff="2026-11-25", use_git=False)


def test_cli_json_and_pr909_dry_run_git_regression_guards(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI JSON output and real repo PR #909 cutoff dry-run regression guard check."""
    ledger = tmp_path / "inv.jsonl"
    ledger.write_text(
        json.dumps(
            _make_event(
                conv="c1",
                turn=1,
                created_at="2026-11-25T16:00:00Z",
                invoked_skill="ccba-ask",
                recommended_commands=["/ccba-grilling"],
            )
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(
        [
            "--skill",
            "ccba-ask",
            "--cutoff",
            DEFAULT_PR909_CUTOFF_UTC,
            "--ledger",
            str(ledger),
            "--drift-check",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["skill"] == "ccba-ask"
    assert parsed["cutoff_utc"] == "2026-11-25T14:32:25+00:00"
    assert parsed["post"]["confirmed"]["invocations"] == 1
    assert "drift_check" in parsed
    assert parsed["regression_guards"]["total_skill_commits"] >= 1

    # Also verify CLI script subprocess invocation parity
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/governance/audit_skill_effectiveness.py",
            "--ledger",
            str(ledger),
            "--no-git",
            "--format",
            "markdown",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0
    assert "Skill Effectiveness Pre/Post A/B Audit" in proc.stdout
