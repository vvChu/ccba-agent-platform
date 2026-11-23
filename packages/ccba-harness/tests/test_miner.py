# packages/ccba-harness/tests/test_miner.py
"""test_miner.py - Unit tests for ccba_harness.evals.miner Deep Seam."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccba_harness.evals.miner import (
    classify_target_skill,
    extract_clean_user_prompt,
    generate_eval_spec_item,
    identify_failures,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
    to_canonical_skill_name,
    to_legacy_skill_name,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_redact_sensitive_info_keys():
    text = "Here is my secret sk-ant-api03-12345678901234567890 and test@example.com"
    redacted = redact_sensitive_info(text)
    assert "sk-ant-" not in redacted
    assert "[API_KEY_REDACTED]" in redacted
    assert "test@example.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted


def test_extract_clean_user_prompt():
    raw = "<USER_REQUEST>Kiểm tra bậc chịu lửa PCCC</USER_REQUEST><SYSTEM_MESSAGE>info</SYSTEM_MESSAGE>"
    cleaned = extract_clean_user_prompt(raw)
    assert cleaned == "Kiểm tra bậc chịu lửa PCCC"


def test_canonical_and_legacy_skill_name_conversion():
    assert to_canonical_skill_name("pccc_audit") == "ccba-ai-qc-pccc-audit"
    assert to_legacy_skill_name("ccba-ai-qc-pccc-audit") == "pccc_audit"


def test_classify_target_skill():
    res = classify_target_skill("Kiểm tra bậc chịu lửa và thoát nạn PCCC theo QCVN 06")
    assert "pccc" in res.lower()

    general = classify_target_skill("Xin chào bạn, hôm nay thời tiết thế nào?")
    assert general == "general_domain"


def test_generate_eval_spec_item_harness_and_legacy():
    fcase = {
        "user_prompt": "Kiểm tra an toàn PCCC",
        "failure_type": "ROUTER_DISCLAIMER",
        "reason": "Agent refused to answer",
        "source_file": "transcript.jsonl",
        "conversation_id": "conv_123",
        "step_index": 1,
    }
    harness_spec = generate_eval_spec_item(fcase, "ccba-ai-qc-pccc-audit", 1, format_type="harness")
    assert harness_spec["input_prompt"] == "Kiểm tra an toàn PCCC"
    assert harness_spec["metadata"]["failure_type"] == "ROUTER_DISCLAIMER"

    legacy_spec = generate_eval_spec_item(fcase, "ccba-ai-qc-pccc-audit", 1, format_type="legacy")
    assert legacy_spec["prompt"] == "Kiểm tra an toàn PCCC"
    assert legacy_spec["id"] == "test_pccc_audit_mined_01"


def test_mine_logs_and_export_dry_run(tmp_path: Path):
    log_file = tmp_path / "transcript.jsonl"
    log_file.write_text(
        '{"type": "USER_INPUT", "content": "Thẩm định bậc chịu lửa và lối thoát hiểm PCCC", "step_index": 1}\n'
        '{"type": "PLANNER_RESPONSE", "content": "Tôi là trợ lý AI, không hỗ trợ tư vấn PCCC.", "step_index": 2}\n',
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    scratch_dir = tmp_path / "scratch"
    count = mine_logs_and_export(
        log_dir=tmp_path,
        output_dir=out_dir,
        dry_run=True,
        scratch_dir=scratch_dir,
    )
    assert count == 1
    assert not out_dir.exists()
    assert scratch_dir.exists()


def test_system_message_with_benign_error_word_not_flagged(tmp_path: Path):
    log_file = tmp_path / "transcript.jsonl"
    rows = [
        {
            "type": "USER_INPUT",
            "content": "Kiểm tra quy trình nghiệm thu thiết kế",
            "step_index": 1,
        },
        {
            "type": "SYSTEM_MESSAGE",
            "status": "DONE",
            "content": "Plan mode is off. Verify 0 console errors before completion.",
            "step_index": 2,
        },
        {
            "type": "SYSTEM_MESSAGE",
            "status": "ERROR",
            "content": "System dispatch failed",
            "step_index": 3,
        },
    ]
    log_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    failures = identify_failures(parse_transcript_logs(tmp_path), taxonomy_filter="TOOL_EXCEPTION")
    assert [f["step_index"] for f in failures] == [3]


def test_generic_done_with_traceback_text_not_flagged(tmp_path: Path):
    log_file = tmp_path / "transcript.jsonl"
    rows = [
        {
            "type": "USER_INPUT",
            "content": "Kiểm tra source code của harness miner",
            "step_index": 1,
        },
        {
            "type": "GENERIC",
            "status": "DONE",
            "content": '259: if status == "ERROR" or "Traceback (most recent call last)" in s:',
            "step_index": 2,
        },
    ]
    log_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    failures = identify_failures(parse_transcript_logs(tmp_path), taxonomy_filter="TOOL_EXCEPTION")
    assert failures == []


def test_generic_error_captured_across_control_commands(tmp_path: Path):
    log_file = tmp_path / "transcript.jsonl"
    prompt = "/ccba-grilling Chốt phạm vi và thiết kế nghiệp vụ Sóng 4"
    rows = [
        {"type": "USER_INPUT", "content": prompt, "step_index": 1},
        {"type": "PLANNER_RESPONSE", "content": "Bạn đồng ý phương án Q1 không?", "step_index": 2},
        {"type": "USER_INPUT", "content": "đồng ý", "step_index": 3},
        {"type": "USER_INPUT", "content": "proceed", "step_index": 4},
        {
            "type": "GENERIC",
            "status": "ERROR",
            "content": "Encountered error in step execution: file does not exist",
            "step_index": 5,
        },
    ]
    log_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    failures = identify_failures(parse_transcript_logs(tmp_path), taxonomy_filter="TOOL_EXCEPTION")
    assert len(failures) == 1
    assert failures[0]["step_index"] == 5
    assert failures[0]["user_prompt"] == prompt


def test_legacy_tool_execution_and_planner_response_backwards_compat(tmp_path: Path):
    log_file = tmp_path / "transcript.jsonl"
    rows = [
        {"type": "USER_INPUT", "content": "Thẩm định bậc chịu lửa nhà cao tầng", "step_index": 1},
        {
            "type": "TOOL_EXECUTION",
            "status": "ERROR",
            "content": "Tool timed out",
            "step_index": 2,
        },
        {
            "type": "RUN_COMMAND",
            "status": "DONE",
            "content": "Traceback (most recent call last):\n  File x.py\nRuntimeError: boom",
            "step_index": 3,
        },
        {
            "type": "PLANNER_RESPONSE",
            "content": "Tôi là trợ lý AI, không hỗ trợ tư vấn PCCC.",
            "step_index": 4,
        },
    ]
    log_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    failures = identify_failures(parse_transcript_logs(tmp_path))
    assert [(f["step_index"], f["failure_type"]) for f in failures] == [
        (2, "TOOL_EXCEPTION"),
        (3, "TOOL_EXCEPTION"),
        (4, "ROUTER_DISCLAIMER"),
    ]
