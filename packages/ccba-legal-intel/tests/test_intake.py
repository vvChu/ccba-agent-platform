"""Tests for Smart Intake Taxonomy and Guided Interview component."""

from ccba_legal.intake import (
    IntakeTaxonomy,
    generate_guided_interview_prompt,
    get_missing_intake_fields,
    parse_intake_question,
)


def test_parse_intake_question_full_coordinates() -> None:
    """Test parsing a question that contains all 5 coordinates."""
    question = (
        "Năm 2026, Chủ đầu tư tiến hành thẩm định thiết kế PCCC cho công trình cấp I tại Hà Nội "
        "thì bị tạm đình chỉ thi công do hết hiệu lực văn bản."
    )
    result = parse_intake_question(question)

    assert isinstance(result, IntakeTaxonomy)
    assert result.subject == "Chủ đầu tư"
    assert result.action == "thẩm định thiết kế PCCC"
    assert result.impact == "tạm đình chỉ thi công"
    assert result.scope == "công trình cấp I"
    assert result.time_timestamp == "2026"


def test_parse_intake_question_missing_coordinates() -> None:
    """Test parsing a question missing time and scope coordinates."""
    question = "Nhà thầu bị đình chỉ nghiệm thu do quy định mới."
    result = parse_intake_question(question)

    assert result.subject == "Nhà thầu"
    assert result.action == "nghiệm thu"
    assert result.impact == "đình chỉ"
    assert result.scope is None
    assert result.time_timestamp is None


def test_get_missing_intake_fields() -> None:
    """Test identifying missing fields in an intake taxonomy."""
    intake = IntakeTaxonomy(
        subject="Tư vấn thẩm tra",
        action="thẩm tra thiết kế",
        impact="xung đột quy chuẩn",
        scope=None,
        time_timestamp=None,
    )
    missing = get_missing_intake_fields(intake)
    assert "scope" in missing
    assert "time_timestamp" in missing
    assert "subject" not in missing


def test_generate_guided_interview_prompt() -> None:
    """Test generating guided interview prompt for missing intake fields."""
    missing = ["scope", "time_timestamp"]
    prompt = generate_guided_interview_prompt(missing)

    assert "Phạm vi" in prompt
    assert "Thời điểm" in prompt
    assert "định danh" in prompt.lower() or "dữ kiện" in prompt.lower()
