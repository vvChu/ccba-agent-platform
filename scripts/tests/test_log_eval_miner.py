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
    clear_catalog_cache,
    extract_clean_user_prompt,
    find_transcript_files,
    generate_eval_spec_item,
    identify_failures,
    load_catalog,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
    resolve_catalog_path,
    resolve_log_dir,
    resolve_output_test_file,
    score_skill_match,
    to_canonical_skill_name,
    to_legacy_skill_name,
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


def test_load_catalog(tmp_path: Path):
    """Test loading catalog.yaml as Single Source of Truth (SSOT)."""
    # 0. Path resolution
    default_cat_path = resolve_catalog_path()
    assert default_cat_path.exists()
    assert default_cat_path.name == "catalog.yaml"

    # 1. Default catalog loads >= 71 skills with names and triggers
    skills = load_catalog()
    assert len(skills) >= 71
    names = {s.get("name") for s in skills}
    assert "ccba-ai-qc-pccc-audit" in names
    assert "bigbim-classification" in names
    assert "platform-loader" in names
    assert "ccba-copywriting" in names

    # 2. Custom catalog loading
    custom_cat = tmp_path / "custom_catalog.yaml"
    custom_cat.write_text(
        "skills:\n"
        "  - name: custom-skill\n"
        "    triggers: ['tùy biến', 'custom']\n",
        encoding="utf-8",
    )
    custom_skills = load_catalog(custom_cat, reload=True)
    assert len(custom_skills) == 1
    assert custom_skills[0]["name"] == "custom-skill"

    # 3. Non-existent catalog returns empty list safely
    non_existent = tmp_path / "does_not_exist.yaml"
    empty_skills = load_catalog(non_existent, reload=True)
    assert empty_skills == []

    # Reset cache to default
    clear_catalog_cache()


def test_classify_target_skill_canonical():
    """Test automatic classification of user prompts into canonical target skills."""
    assert classify_target_skill("Soạn thảo hợp đồng và công văn gửi đối tác") == "ccba-copywriting"
    assert classify_target_skill("Kiểm tra bậc chịu lửa PCCC và kiểm soát khói") == "ccba-ai-qc-pccc-audit"
    assert (
        classify_target_skill("Nghiên cứu văn bản pháp điển Nghị định 105/2025/NĐ-CP")
        == "ccba-legal-intel"
    )
    assert classify_target_skill("Viết bài báo khoa học cấu trúc IMRAD") == "ccba-academic-writing"
    assert classify_target_skill("Phân loại mã IFC Uniclass theo BIM") == "bigbim-classification"
    assert classify_target_skill("Tính năng khác không rõ") == "general_domain"


def test_classify_target_skill_legacy_backward_compatibility():
    """Test backward compatibility mode returning legacy shorthand skill names."""
    assert (
        classify_target_skill("Soạn thảo hợp đồng và công văn gửi đối tác", canonical=False)
        == "copywriting"
    )
    assert (
        classify_target_skill("Kiểm tra bậc chịu lửa PCCC và kiểm soát khói", canonical=False)
        == "pccc_audit"
    )
    assert (
        classify_target_skill(
            "Nghiên cứu văn bản pháp điển Nghị định 105/2025/NĐ-CP", canonical=False
        )
        == "legal_intel"
    )
    assert (
        classify_target_skill("Viết bài báo khoa học cấu trúc IMRAD", canonical=False)
        == "academic_writing"
    )
    assert (
        classify_target_skill("Phân loại mã IFC Uniclass theo BIM", canonical=False)
        == "bigbim_classification"
    )
    assert classify_target_skill("Tính năng khác không rõ", canonical=False) == "general_domain"


def test_regression_no_false_positive_tham_tra():
    """Regression prevention: generic 'thẩm tra' prompts must NOT route to pccc_audit without fire safety keywords."""
    # Prompts containing 'thẩm tra' but NO fire safety keywords -> Must NOT be pccc_audit or ccba-ai-qc-pccc-audit
    generic_prompts = [
        "Thẩm tra catalog và lint codebase",
        "Nhiệm vụ: Thẩm tra và đồng bộ hóa catalog.yaml cùng các tài liệu chính của hệ thống",
        "Thẩm tra cấu trúc thư mục .agents và workflows",
        "Thẩm tra báo cáo tiến độ và nghiệm thu công việc nội bộ",
        "Tiến hành thẩm tra tài liệu kỹ thuật dự án",
    ]
    for prompt in generic_prompts:
        canonical_result = classify_target_skill(prompt, canonical=True)
        assert canonical_result != "ccba-ai-qc-pccc-audit", f"False positive PCCC audit on: '{prompt}'"
        legacy_result = classify_target_skill(prompt, canonical=False)
        assert legacy_result != "pccc_audit", f"False positive PCCC audit on: '{prompt}'"

    # Prompts containing fire safety keywords WITH 'thẩm tra' -> MUST route to PCCC audit
    pccc_prompts = [
        "Thẩm tra PCCC theo QCVN 06:2022 và kiểm tra bậc chịu lửa",
        "Thẩm tra thiết kế phòng cháy chữa cháy công trình",
        "Kiểm tra hệ thống báo cháy và thiết bị chữa cháy tự động",
        "Thẩm tra giải pháp thoát nạn và kiểm soát khói hành lang",
    ]
    for prompt in pccc_prompts:
        assert classify_target_skill(prompt, canonical=True) == "ccba-ai-qc-pccc-audit"
        assert classify_target_skill(prompt, canonical=False) == "pccc_audit"


def test_classify_trigger_matching_and_specificity():
    """Test exact command triggers, multi-word specificity weighting, and word boundary matching."""
    # 1. Exact command trigger (/ccba-...)
    assert classify_target_skill("Vui lòng chạy /ccba-mermaid-diagram cho kiến trúc") == "ccba-mermaid-diagram"

    # 2. Canonical skill name in text
    assert (
        classify_target_skill("Cần dùng ccba-api-circuit-breaker bảo vệ rate limit")
        == "ccba-api-circuit-breaker"
    )

    # 3. Word boundary: 'ai' shouldn't trigger ccba-ai-gateway-sdk inside words
    assert classify_target_skill("Đây là bài phát biểu tại hội nghị") == "general_domain"

    # 4. Multi-word trigger matching
    assert classify_target_skill("Phân tích RASE cho mô hình IFC4X3") == "bigbim-rase"
    assert classify_target_skill("Che giấu API key bằng maskara") == "ccba-maskara"


def test_classify_disambiguation():
    """Test disambiguation between competing skills (orchestration vs domain, advisor vs tracker)."""
    # Agent orchestration cues
    assert (
        classify_target_skill("You are Forensic Auditor 1 for Milestone 1")
        == "ccba-teamwork"
    )
    assert (
        classify_target_skill("You are Forensic Auditor 1 for Milestone 1", canonical=False)
        == "agent_orchestration"
    )
    assert (
        classify_target_skill("You are teamwork_preview_explorer_m1_1")
        == "ccba-teamwork"
    )

    # Legal advisor vs legal document tracker
    assert (
        classify_target_skill("Tư vấn pháp lý về hồ sơ cấp phép xây dựng")
        == "ccba-legal-advisor"
    )
    assert (
        classify_target_skill("Tra cứu cập nhật thông tư và nghị định trong registry VBPL")
        == "ccba-legal-document-tracker"
    )


def test_resolve_output_test_file(tmp_path: Path):
    """Test output test suite file resolution preserving backward compatibility."""
    out_dir = tmp_path / "test_cases"
    out_dir.mkdir()

    # Mapped skills resolve to legacy filename even if not on disk yet
    assert resolve_output_test_file(out_dir, "ccba-ai-qc-pccc-audit") == out_dir / "eval_pccc_audit.json"
    assert resolve_output_test_file(out_dir, "pccc_audit") == out_dir / "eval_pccc_audit.json"
    assert resolve_output_test_file(out_dir, "ccba-legal-intel") == out_dir / "eval_legal_intel.json"
    assert resolve_output_test_file(out_dir, "bigbim-classification") == out_dir / "eval_bigbim_classification.json"
    assert resolve_output_test_file(out_dir, "general_domain") == out_dir / "eval_general_domain.json"

    # Unmapped canonical skill creates standardized snake_case file
    assert resolve_output_test_file(out_dir, "ccba-maskara") == out_dir / "eval_ccba_maskara.json"

    # If an existing file is present on disk (e.g. eval_ccba-maskara.json), preserve it
    existing_file = out_dir / "eval_ccba-maskara.json"
    existing_file.write_text("[]", encoding="utf-8")
    assert resolve_output_test_file(out_dir, "ccba-maskara") == existing_file


def test_skill_name_conversions():
    """Test bidirectional name conversion helpers."""
    assert to_canonical_skill_name("pccc_audit") == "ccba-ai-qc-pccc-audit"
    assert to_canonical_skill_name("legal_intel") == "ccba-legal-intel"
    assert to_legacy_skill_name("ccba-ai-qc-pccc-audit") == "pccc_audit"
    assert to_legacy_skill_name("ccba-legal-intel") == "legal_intel"
    assert to_legacy_skill_name("ccba-unknown-skill") == "unknown_skill"


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
        json.dumps({"type": "USER_INPUT", "content": "Soạn thảo hợp đồng tư vấn thiết kế"}) + "\n",
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


def test_edge_case_null_and_empty_inputs(tmp_path: Path):
    """Test robustness against None and empty string inputs across public APIs."""
    assert classify_target_skill(None) == "general_domain"
    assert classify_target_skill("") == "general_domain"
    assert classify_target_skill("   ") == "general_domain"
    assert score_skill_match({}, None) == 0.0
    assert score_skill_match({}, "") == 0.0
    assert to_canonical_skill_name(None) == ""
    assert to_canonical_skill_name("") == ""
    assert to_legacy_skill_name(None) == ""
    assert to_legacy_skill_name("") == ""
    assert resolve_output_test_file(tmp_path, "") == tmp_path / "eval_general_domain.json"
    assert resolve_output_test_file(tmp_path, None) == tmp_path / "eval_general_domain.json"


def test_regression_diacritic_chat_collision():
    """Regression: Vietnamese 'chất' (chất lượng) must NOT falsely trigger English 'chat' in ccba-ai-gateway-sdk."""
    # Prompt about design quality audit -> must route to ccba-ai-qc, NOT ccba-ai-gateway-sdk
    design_quality_prompt = "Thẩm tra chất lượng thiết kế đa bộ môn cho dự án"
    assert classify_target_skill(design_quality_prompt) == "ccba-ai-qc"
    assert classify_target_skill(design_quality_prompt) != "ccba-ai-gateway-sdk"

    # General construction quality prompt -> must NOT route to ccba-ai-gateway-sdk
    const_quality_prompt = "Đảm bảo chất lượng công trình xây dựng theo tiêu chuẩn"
    assert classify_target_skill(const_quality_prompt) != "ccba-ai-gateway-sdk"

    # Legitimate AI chat prompt -> MUST route to ccba-ai-gateway-sdk
    legit_ai_prompt = "Nhắn tin chat trực tiếp với mô hình LLM qua Gateway"
    assert classify_target_skill(legit_ai_prompt) == "ccba-ai-gateway-sdk"


def test_classify_spaced_canonical_skill_names():
    """Test classification when user mentions natural space-separated skill names."""
    assert (
        classify_target_skill("Thực hiện code review cho pull request này")
        == "ccba-code-review"
    )
    assert (
        classify_target_skill("Thiết lập api circuit breaker để chống nghẽn")
        == "ccba-api-circuit-breaker"
    )
    assert (
        classify_target_skill("Thiết lập git guardrails bảo vệ commit")
        == "ccba-git-guardrails"
    )
    assert (
        classify_target_skill("Tạo danh mục completion checklist cho dự án")
        == "ccba-completion-checklist"
    )


def test_dynamic_canonical_skill_resolution():
    """Test dynamic resolution of shorthand names to canonical names using catalog."""
    assert to_canonical_skill_name("ai_qc") == "ccba-ai-qc"
    assert to_canonical_skill_name("git_guardrails") == "ccba-git-guardrails"
    assert to_canonical_skill_name("maskara") == "ccba-maskara"
    assert to_canonical_skill_name("classification") == "bigbim-classification"


def test_custom_catalog_path_in_miner(tmp_path: Path):
    """Test mine_logs_and_export with custom catalog_path."""
    custom_cat = tmp_path / "custom_catalog.yaml"
    custom_cat.write_text(
        "skills:\n"
        "  - name: ccba-custom-tester\n"
        "    triggers: ['thử nghiệm đặc biệt']\n",
        encoding="utf-8",
    )

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "transcript.jsonl"
    lines = [
        json.dumps({"type": "USER_INPUT", "content": "Yêu cầu thử nghiệm đặc biệt này"}) + "\n",
        json.dumps(
            {
                "type": "PLANNER_RESPONSE",
                "step_index": 1,
                "content": "Tôi là trợ lý, không thuộc phạm vi xử lý.",
            }
        )
        + "\n",
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    out_dir = tmp_path / "test_cases"
    count = mine_logs_and_export(
        log_dir,
        out_dir,
        catalog_path=custom_cat,
        format_type="harness",
    )
    assert count == 1
    target_json = out_dir / "eval_ccba_custom_tester.json"
    assert target_json.exists()

