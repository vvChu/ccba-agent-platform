# packages/ccba-harness/tests/test_miner.py
"""test_miner.py - Unit tests for ccba_harness.evals.miner Deep Seam."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals.miner import (
    classify_target_skill,
    extract_clean_user_prompt,
    generate_eval_spec_item,
    mine_logs_and_export,
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
