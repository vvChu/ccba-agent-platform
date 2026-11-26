"""test_turn_stream_and_probes.py - Wave 1 unit tests for Canonical Turn Stream & Zero-LLM Probes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import ccba_harness
from ccba_harness.evals._turn_stream import (
    UserTurn,
    build_invocation_event,
    detect_behavioral_probes,
    detect_routing_contract_drift,
    detect_side_effect_violation,
    extract_slash_invocation,
    record_skill_invocations,
    stream_user_turns,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8"
    )
    return path


def test_turn_stream_module_stays_private() -> None:
    """Verify COND-LOC-HEADROOM: private _turn_stream helpers are NOT exported in ccba_harness.__all__."""
    assert "_turn_stream" not in ccba_harness.__all__
    assert "stream_user_turns" not in ccba_harness.__all__
    assert "record_skill_invocations" not in ccba_harness.__all__


def test_extract_slash_invocation_separates_invoked_vs_mentioned() -> None:
    """Verify +100 leading slash precedence, clause-head invocation, and meta-discussion filtering."""
    cmap = {
        "/ccba-ask": "ccba-ask",
        "/ccba-research": "ccba-research",
        "/ccba-grilling": "ccba-grilling",
    }

    skill, cmd, mentions = extract_slash_invocation(
        "/ccba-ask tôi dùng skill /plan được không?", cmap
    )
    assert skill == "ccba-ask"
    assert cmd == "/ccba-ask"
    assert mentions == ["/plan"]

    skill2, cmd2, mentions2 = extract_slash_invocation("/ccba-ask", cmap)
    assert skill2 == "ccba-ask"
    assert cmd2 == "/ccba-ask"
    assert mentions2 == []

    skill3, cmd3, mentions3 = extract_slash_invocation(
        "/ccba-research bài học rút ra từ skill /ccba-ask là gì?", cmap
    )
    assert skill3 == "ccba-research"
    assert cmd3 == "/ccba-research"
    assert mentions3 == ["/ccba-ask"]

    skill4, cmd4, mentions4 = extract_slash_invocation(
        "triển khai luôn Bước 1 + Bước 2, /ccba-ask có cần chạy lệnh /plan ?", cmap
    )
    assert skill4 == "ccba-ask"
    assert cmd4 == "/ccba-ask"
    assert mentions4 == ["/plan"]

    skill5, cmd5, mentions5 = extract_slash_invocation(
        "Hãy đánh giá đề xuất trên của skill /ccba-ask nhé", cmap
    )
    assert skill5 is None
    assert cmd5 is None
    assert mentions5 == ["/ccba-ask"]


def test_stream_user_turns_preserves_short_prompts_all_responses_and_tools(tmp_path: Path) -> None:
    """Verify bare /ccba-ask (9 chars), short confirmations, multi-step responses, and tool calls."""
    log_path = tmp_path / "conv-abc" / ".system_generated" / "logs" / "transcript.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                "step_index": 1,
                "type": "USER_INPUT",
                "created_at": "2026-11-25T10:00:00Z",
                "content": "<USER_REQUEST>\n/ccba-ask\n</USER_REQUEST><ADDITIONAL_METADATA>time</ADDITIONAL_METADATA>",
            },
            {
                "step_index": 2,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-25T10:00:02Z",
                "content": "Đang đọc trạng thái repo...",
                "tool_calls": [
                    {
                        "name": "read_file",
                        "args": {"Path": "/home/vvc/ccba/ccba-agent-platform/AGENTS.md"},
                    }
                ],
            },
            {
                "step_index": 3,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-25T10:00:05Z",
                "content": "Khuyến nghị chạy `/ccba-release-feature` để hoàn tất.",
                "tool_calls": [],
            },
            {
                "step_index": 4,
                "type": "USER_INPUT",
                "created_at": "2026-11-25T10:01:00Z",
                "content": "<USER_REQUEST>1</USER_REQUEST>",
            },
            {
                "step_index": 5,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-25T10:01:02Z",
                "content": "Đã xác nhận phương án 1.",
                "tool_calls": [],
            },
        ],
    )

    turns = stream_user_turns(log_path)
    assert len(turns) == 2

    t1 = turns[0]
    assert t1.conversation_id == "conv-abc"
    assert t1.invoked_skill == "ccba-ask"
    assert t1.user_prompt == "/ccba-ask"
    assert len(t1.user_prompt) == 9
    assert t1.planner_steps == 2
    assert len(t1.planner_responses) == 2
    assert "/ccba-release-feature" in t1.recommended_commands
    assert t1.tool_counts == {"read_file": 1}
    assert t1.mutating_tool_count == 0
    assert len(t1.workspace_hash) == 16
    assert "ccba-agent-platform" not in t1.workspace_hash
    assert t1.tool_calls[0].target_basename == "AGENTS.md"

    t2 = turns[1]
    assert t2.user_prompt == "1"
    assert t2.invoked_skill is None
    assert t2.workspace_hash == t1.workspace_hash


def test_side_effect_violation_probe_rules(tmp_path: Path) -> None:
    """Verify SIDE_EFFECT_VIOLATION catches /plan write leak and obeys COND-MINER-SSOT."""
    log_path = tmp_path / "conv-leak" / ".system_generated" / "logs" / "transcript.jsonl"
    _write_jsonl(
        log_path,
        [
            # Case 1: /ccba-ask mentioning /plan and leaking write_file -> VIOLATION
            {
                "step_index": 10,
                "type": "USER_INPUT",
                "created_at": "2026-11-08T08:44:29Z",
                "content": "<USER_REQUEST>/ccba-ask tôi dùng skill /plan được không?</USER_REQUEST>",
            },
            {
                "step_index": 11,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-08T08:44:35Z",
                "content": "Đã lập kế hoạch.",
                "tool_calls": [
                    {"name": "read_file", "args": {"Path": "/home/vvc/ccba/demo/SKILL.md"}},
                    {
                        "name": "write_file",
                        "args": {"Path": "/home/vvc/brain/implementation_plan.md"},
                    },
                ],
            },
            # Case 2: /ccba-ask with missing tool_calls -> NO violation (COND-MINER-SSOT)
            {
                "step_index": 20,
                "type": "USER_INPUT",
                "created_at": "2026-11-08T08:50:00Z",
                "content": "<USER_REQUEST>/ccba-ask tiếp theo làm gì?</USER_REQUEST>",
            },
            {
                "step_index": 21,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-08T08:50:05Z",
                "content": "Chạy `/ccba-create-pr`.",
            },
            # Case 3: /ccba-ask with read-only tools only -> NO violation
            {
                "step_index": 30,
                "type": "USER_INPUT",
                "created_at": "2026-11-08T09:00:00Z",
                "content": "<USER_REQUEST>/ccba-ask nên dùng /plan hay /ccba-grilling?</USER_REQUEST>",
            },
            {
                "step_index": 31,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-08T09:00:05Z",
                "content": "Dùng `/ccba-grilling` trước.",
                "tool_calls": [{"name": "read_file", "args": {"Path": "/tmp/a.md"}}],
            },
            # Case 4: /ccba-ask Mode B brainstorm doc write (no mentioned commands) -> ALLOWED
            {
                "step_index": 40,
                "type": "USER_INPUT",
                "created_at": "2026-11-08T09:10:00Z",
                "content": "<USER_REQUEST>/ccba-ask brainstorm kiến trúc telemetry mới</USER_REQUEST>",
            },
            {
                "step_index": 41,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-08T09:10:15Z",
                "content": "Đã lưu hồ sơ brainstorm.",
                "tool_calls": [
                    {
                        "name": "write_file",
                        "args": {"Path": "/home/vvc/ccba/demo/.md/brainstorm-session-telemetry.md"},
                    }
                ],
            },
        ],
    )

    turns = stream_user_turns(log_path)
    violations = [v for t in turns if (v := detect_side_effect_violation(t)) is not None]
    assert len(violations) == 1
    assert violations[0].step_index == 10
    assert violations[0].probe_type == "SIDE_EFFECT_VIOLATION"
    assert violations[0].confidence == "confirmed"
    assert violations[0].details["mutating_tools"] == ["write_file"]
    assert violations[0].details["mentioned_commands"] == ["/plan"]


def test_routing_contract_drift_and_noise_filtering(tmp_path: Path) -> None:
    """Verify ROUTING_CONTRACT_DRIFT catches unregistered CCBA commands and ignores code/typos/SYSTEM_MESSAGE."""
    valid = frozenset({"/ccba-ask", "/ccba-grilling", "/plan"})
    drift_turn = UserTurn(
        conversation_id="c1",
        turn_index=1,
        step_index=1,
        created_at="2026-11-25T10:00:00Z",
        workspace_hash="abcd1234abcd1234",
        user_prompt="/ccba-ask nên chạy lệnh nào?",
        invoked_skill="ccba-ask",
        recommended_commands=["/ccba-grilling", "/ccba-hallucinated-magic", "/plan"],
    )
    finding = detect_routing_contract_drift(drift_turn, valid_commands=valid)
    assert finding is not None
    assert finding.probe_type == "ROUTING_CONTRACT_DRIFT"
    assert finding.details["unregistered_commands"] == ["/ccba-hallucinated-magic"]

    # Echoing user's own typo should NOT be flagged as assistant drift
    typo_turn = UserTurn(
        conversation_id="c1",
        turn_index=2,
        step_index=5,
        created_at="2026-11-25T10:01:00Z",
        workspace_hash="abcd1234abcd1234",
        user_prompt="/ccba-ask sao /ccba-typo-cmd không chạy?",
        invoked_skill="ccba-ask",
        recommended_commands=["/ccba-typo-cmd", "/plan"],
    )
    assert detect_routing_contract_drift(typo_turn, valid_commands=valid) is None

    # SYSTEM_MESSAGE errors & inline pytest smoke errors are filtered out
    log_path = tmp_path / "conv-noise" / ".system_generated" / "logs" / "transcript.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                "step_index": 1,
                "type": "USER_INPUT",
                "content": "<USER_REQUEST>/ccba-ask</USER_REQUEST>",
            },
            {
                "step_index": 2,
                "type": "SYSTEM_MESSAGE",
                "status": "ERROR",
                "content": "system notice",
            },
            {
                "step_index": 3,
                "type": "RUN_COMMAND",
                "status": "ERROR",
                "content": "Traceback (most recent call last):\npytest inline smoke failed",
            },
            {
                "step_index": 4,
                "type": "PLANNER_RESPONSE",
                "content": "```bash\n/ccba-fake-in-code\n```",
            },
        ],
    )
    noise_turns = stream_user_turns(log_path)
    assert detect_behavioral_probes(noise_turns) == []


def test_record_skill_invocations_idempotent_and_zero_raw_prompt_privacy(tmp_path: Path) -> None:
    """Verify .md/telemetry/skill_invocations.jsonl is idempotent with zero raw prompt/paths/PII."""
    sample_val = "sk-" + "ant-api03-" + "9876543210abcdef9876543210"
    raw_prompt = (
        f"/ccba-ask kiểm tra /plan cho user@secret.vn val {sample_val} tại /home/vvc/private/client"
    )
    log_path = tmp_path / "conv-priv" / ".system_generated" / "logs" / "transcript.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                "step_index": 1,
                "type": "USER_INPUT",
                "created_at": "2026-11-25T15:00:00Z",
                "content": f"<USER_REQUEST>{raw_prompt}</USER_REQUEST>",
            },
            {
                "step_index": 2,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-25T15:00:05Z",
                "content": "Nên dùng `/ccba-grilling` trước.",
                "tool_calls": [
                    {
                        "name": "write_file",
                        "args": {"Path": "/home/vvc/private/client/implementation_plan.md"},
                    }
                ],
            },
            {
                "step_index": 3,
                "type": "USER_INPUT",
                "created_at": "2026-11-25T15:01:00Z",
                "content": "<USER_REQUEST>đồng ý</USER_REQUEST>",
            },
            {
                "step_index": 4,
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-25T15:01:05Z",
                "content": "OK.",
            },
        ],
    )

    turns = stream_user_turns(log_path)
    ledger = tmp_path / ".md" / "telemetry" / "skill_invocations.jsonl"
    added_1 = record_skill_invocations(turns, ledger_path=ledger)
    added_2 = record_skill_invocations(turns, ledger_path=ledger)
    assert added_1 == 2
    assert added_2 == 0

    raw_ledger = ledger.read_text(encoding="utf-8")
    assert "user@secret.vn" not in raw_ledger
    assert sample_val not in raw_ledger
    assert "/home/vvc/private/client" not in raw_ledger
    assert "kiểm tra" not in raw_ledger
    assert "Nên dùng" not in raw_ledger

    rows = [json.loads(line) for line in raw_ledger.splitlines() if line.strip()]
    assert len(rows) == 2
    assert rows[0]["event_id"] == "conv-priv:1"
    assert rows[0]["invoked_skill"] == "ccba-ask"
    assert rows[0]["mentioned_commands"] == ["/plan"]
    assert rows[0]["recommended_commands"] == ["/ccba-grilling"]
    assert rows[0]["mutating_tool_count"] == 1
    assert "SIDE_EFFECT_VIOLATION" in rows[0]["probe_violations"]
    assert rows[1]["is_short_confirmation"] is True

    # Ensure build_invocation_event never includes raw prompt/response keys
    ev = build_invocation_event(turns[0], ["SIDE_EFFECT_VIOLATION"])
    assert "user_prompt" not in ev
    assert "planner_response" not in ev
    assert "project_path" not in ev
