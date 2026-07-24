#!/usr/bin/env python3
"""test_log_eval_miner.py - Unit tests for log_eval_miner.py."""

import json
import pytest
from pathlib import Path

from scripts.log_eval_miner import (
    generate_synthetic_test_case,
    identify_router_failures,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
)


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


def test_parse_transcript_logs(tmp_path: Path):
    """Test parsing user prompts from transcript.jsonl."""
    log_file = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps({"type": "USER_INPUT", "content": "Hỏi về Nghị định 105/2025/NĐ-CP SĐT 0987654321"}) + "\n",
        json.dumps({"type": "PLANNER_RESPONSE", "step_index": 1, "content": "Tôi là trợ lý PCCC..."}) + "\n",
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    interactions = parse_transcript_logs(tmp_path)
    assert len(interactions) == 1
    assert "[PHONE_REDACTED]" in interactions[0]["user_prompt"]
    assert "0987654321" not in interactions[0]["user_prompt"]


def test_identify_router_failures():
    """Test detecting disclaimers or router failures."""
    interactions = [
        {
            "user_prompt": "Hãy viết hàm quicksort Python cho tôi",
            "planner_response": "Tôi là trợ lý copywriting, câu hỏi này không thuộc phạm vi của tôi.",
        },
        {
            "user_prompt": "Soạn văn bản hành chính theo Nghị định 30",
            "planner_response": "Dưới đây là mẫu văn bản hành chính...",
        },
    ]
    failures = identify_router_failures(interactions)
    assert len(failures) == 1
    assert "quicksort" in failures[0]["user_prompt"]


def test_generate_synthetic_test_case():
    """Test synthetic test case structure."""
    case = generate_synthetic_test_case("Prompt kiểm thử lân cận", "copywriting", 1)
    assert case["id"] == "test_copywriting_mined_01"
    assert case["prompt"] == "Prompt kiểm thử lân cận"
    assert len(case["assertions"]) >= 1


def test_mine_logs_and_export(tmp_path: Path):
    """Test end-to-end log mining and JSON export."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "transcript.jsonl"
    lines = [
        json.dumps({"type": "USER_INPUT", "content": "Hãy tính toán tiết diện dầm thép I300"}) + "\n",
        json.dumps({"type": "PLANNER_RESPONSE", "step_index": 1, "content": "Tôi không hỗ trợ tính toán kết cấu..."}) + "\n",
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    out_dir = tmp_path / "test_cases"
    count = mine_logs_and_export(log_dir, out_dir, "copywriting")
    assert count == 1
    target_json = out_dir / "eval_copywriting.json"
    assert target_json.exists()
    data = json.loads(target_json.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert "dầm thép" in data[0]["prompt"]
