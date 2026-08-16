"""test_log_eval_miner.py - Scoped Fast Unit tests for log_eval_miner.py.

Tests sensitive data redaction, multi-type failure taxonomy detection,
EvalItem spec formatting for ccba_harness.evals, prompt sanitization,
skill domain classification, and idempotent mining export.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.eval.log_eval_miner import (
    classify_target_skill,
    extract_clean_user_prompt,
    find_transcript_files,
    generate_eval_spec_item,
    identify_failures,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
    resolve_log_dir,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_resolve_log_dir(tmp_path: Path):
    """Test resolving custom and default log directories."""
    custom = tmp_path / "custom_logs"
    custom.mkdir()
    assert resolve_log_dir(custom) == custom
    resolved_default = resolve_log_dir(None)
    assert resolved_default is not None



def test_redact_sensitive_info():
    """Test redaction of email, phone, API key, and IP address."""
    raw = "Liên hệ user@example.com hoặc SĐT 0912345678 với key sk-abcdef12345678901234567890 tại 100.83.192.30"
    redacted = redact_sensitive_info(raw)
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "[API_KEY_REDACTED]" in redacted
    assert "[IP_REDACTED]" in redacted
    assert "user@example.com" not in redacted
    assert "0912345678" not in redacted


def test_extract_clean_user_prompt():
    """Test extraction of clean prompt from XML envelopes and metadata tags."""
    raw = (
        "<USER_REQUEST>\n"
        "Kiểm tra yêu cầu bậc chịu lửa theo QCVN 06:2022\n"
        "</USER_REQUEST>\n"
        "<ADDITIONAL_METADATA>\n"
        "The current local time is: 2026-08-16T13:50:25+07:00.\n"
        "</ADDITIONAL_METADATA>\n"
        "<USER_SETTINGS_CHANGE>\n"
        "The user changed setting Model Selection.\n"
        "</USER_SETTINGS_CHANGE>"
    )
    cleaned = extract_clean_user_prompt(raw)
    assert cleaned == "Kiểm tra yêu cầu bậc chịu lửa theo QCVN 06:2022"
    assert "ADDITIONAL_METADATA" not in cleaned


def test_classify_target_skill():
    """Test automatic classification of user prompts into target skills."""
    assert classify_target_skill("Soạn thảo hợp đồng và công văn gửi đối tác") == "copywriting"
    assert (
        classify_target_skill("Kiểm tra bậc chịu lửa PCCC và kiểm soát khói")
        == "pccc_audit"
    )
    assert (
        classify_target_skill("Nghiên cứu văn bản pháp điển Nghị định 105/2025/NĐ-CP")
        == "legal_intel"
    )
    assert (
        classify_target_skill("Viết bài báo khoa học cấu trúc IMRAD") == "academic_writing"
    )
    assert classify_target_skill("Phân loại mã IFC Uniclass theo BIM") == "bigbim_classification"
    assert classify_target_skill("Tính năng khác không rõ") == "general_domain"


def test_find_transcript_files(tmp_path: Path):
    """Test resilient traversal of transcript files."""
    d1 = tmp_path / "conv_1" / ".system_generated" / "logs"
    d1.mkdir(parents=True)
    (d1 / "transcript.jsonl").write_text("{}", encoding="utf-8")
    (d1 / "transcript_full.jsonl").write_text("{}", encoding="utf-8")

    files = find_transcript_files(tmp_path)
    assert len(files) == 1
    assert files[0].name == "transcript.jsonl"


def test_parse_transcript_logs(tmp_path: Path):
    """Test parsing user prompts from transcript.jsonl."""
    log_file = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps(
            {"type": "USER_INPUT", "content": "Hỏi về Nghị định 105/2025/NĐ-CP SĐT 0987654321"}
        )
        + "\n",
        json.dumps(
            {"type": "PLANNER_RESPONSE", "step_index": 1, "content": "Tôi là trợ lý PCCC..."}
        )
        + "\n",
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    interactions = parse_transcript_logs(tmp_path)
    assert len(interactions) == 1
    assert "[PHONE_REDACTED]" in interactions[0]["user_prompt"]
    assert "0987654321" not in interactions[0]["user_prompt"]


def test_identify_failures_taxonomy():
    """Test detecting and classifying different failure types."""
    interactions = [
        # Router disclaimer failure
        {
            "user_prompt": "Hãy viết bài nghiên cứu khoa học cho tôi",
            "planner_response": "Tôi là trợ lý copywriting, câu hỏi này không thuộc phạm vi của tôi.",
        },
        # Tool exception failure
        {
            "user_prompt": "Phân tích file bản vẽ CAD layout",
            "planner_response": 'Traceback (most recent call last):\nToolExecutionError: "status": "error"',
        },
        # Outdated decree citation failure
        {
            "user_prompt": "Quy định thẩm duyệt thiết kế PCCC",
            "planner_response": "Căn cứ theo Nghị định 136/2020/NĐ-CP và QCVN 06:2020...",
        },
        # Valid successful response (No failure)
        {
            "user_prompt": "Soạn văn bản hành chính theo Nghị định 30",
            "planner_response": "Dưới đây là mẫu văn bản hành chính chuẩn Nghị định 30/2020/NĐ-CP...",
        },
    ]

    failures = identify_failures(interactions)
    assert len(failures) == 3

    types = {f["failure_type"] for f in failures}
    assert "ROUTER_DISCLAIMER" in types
    assert "TOOL_EXCEPTION" in types
    assert "OUTDATED_CITATION" in types


def test_generate_eval_spec_item_harness_format():
    """Test generating EvalItem dictionary compatible with ccba_harness.evals."""
    fcase = {
        "user_prompt": "Kiểm tra giới hạn chịu lửa theo QCVN 06:2022",
        "failure_type": "ROUTER_DISCLAIMER",
        "reason": "Agent refused valid domain request",
        "source_file": "transcript_1.jsonl",
        "conversation_id": "conv-123",
        "step_index": 4,
    }
    item = generate_eval_spec_item(fcase, "pccc_audit", 1, format_type="harness")

    assert item["id"] == "test_pccc_audit_mined_01"
    assert item["input_prompt"] == "Kiểm tra giới hạn chịu lửa theo QCVN 06:2022"
    assert "Must properly process prompt" in item["rubric"]
    assert item["metadata"]["failure_type"] == "ROUTER_DISCLAIMER"
    assert item["metadata"]["source_file"] == "transcript_1.jsonl"
    assert item["metadata"]["conversation_id"] == "conv-123"


def test_generate_eval_spec_item_legacy_format():
    """Test generating legacy 4-layer assertion format."""
    fcase = {
        "user_prompt": "Prompt kiểm thử lân cận",
        "failure_type": "ROUTER_DISCLAIMER",
        "reason": "Refusal",
    }
    item = generate_eval_spec_item(fcase, "copywriting", 2, format_type="legacy")

    assert item["id"] == "test_copywriting_mined_02"
    assert item["prompt"] == "Prompt kiểm thử lân cận"
    assert len(item["assertions"]) >= 1


def test_mine_logs_and_export_idempotent(tmp_path: Path):
    """Test end-to-end log mining and JSON export with deduplication and auto-grouping."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "transcript.jsonl"
    lines = [
        json.dumps({"type": "USER_INPUT", "content": "Soạn thảo hợp đồng tư vấn thiết kế"})
        + "\n",
        json.dumps(
            {
                "type": "PLANNER_RESPONSE",
                "step_index": 1,
                "content": "Tôi không hỗ trợ tính toán kết cấu...",
            }
        )
        + "\n",
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    out_dir = tmp_path / "test_cases"

    # First run: exports 1 case (classified into copywriting)
    count_1 = mine_logs_and_export(log_dir, out_dir, format_type="harness")
    assert count_1 == 1

    target_json = out_dir / "eval_copywriting.json"
    assert target_json.exists()
    data = json.loads(target_json.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert "hợp đồng" in data[0]["input_prompt"]

    # Second run with same log: should be idempotent (0 duplicate exports)
    count_2 = mine_logs_and_export(log_dir, out_dir, format_type="harness")
    assert count_2 == 0
