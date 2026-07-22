"""Smart Intake Taxonomy & Guided Interview Engine.

Extracts 5-axis legal coordinates (Subject, Action, Impact, Scope, Time)
from user queries and generates guided interview prompts when coordinates are missing.
"""

import re
from dataclasses import dataclass

FIELD_DISPLAY_NAMES = {
    "subject": "Đối tượng (Chủ đầu tư, Nhà thầu, Tư vấn...)",
    "action": "Hành vi (Thẩm định, Phê duyệt, Nghiệm thu...)",
    "impact": "Tác động (Đình chỉ, Xử phạt, Chuyển tiếp...)",
    "scope": "Phạm vi (Cấp/Loại công trình, Quy mô...)",
    "time_timestamp": "Thời điểm (Năm, Ngày áp dụng...)",
}


@dataclass
class IntakeTaxonomy:
    """Dataclass holding 5-axis legal intake coordinates."""

    subject: str | None = None
    action: str | None = None
    impact: str | None = None
    scope: str | None = None
    time_timestamp: str | None = None


def parse_intake_question(text: str) -> IntakeTaxonomy:
    """Parse raw query text into a structured 5-axis IntakeTaxonomy."""
    subject = None
    action = None
    impact = None
    scope = None
    time_timestamp = None

    # Time extraction (e.g. 2026, 2025, tháng 5/2026)
    time_match = re.search(r"\b(20\d{2})\b", text)
    if time_match:
        time_timestamp = time_match.group(1)

    # Scope extraction (e.g. công trình cấp I, cấp II, nhà cao tầng)
    scope_match = re.search(
        r"((công trình\s+)?cấp\s+[I|V|X]+|cấp\s+\d+|nhà cao tầng|quy mô lớn)", text, re.IGNORECASE
    )
    if scope_match:
        scope = scope_match.group(0)

    # Subject extraction
    for kw in ["Chủ đầu tư", "Nhà thầu", "Tư vấn thẩm tra", "Đơn vị thiết kế", "Cơ quan nhà nước"]:
        if kw.lower() in text.lower():
            subject = kw
            break

    # Action extraction
    action_match = re.search(
        r"(thẩm định thiết kế PCCC|nghiệm thu|thẩm tra thiết kế|cấp phép xây dựng|xin ý kiến)",
        text,
        re.IGNORECASE,
    )
    if action_match:
        action = action_match.group(0)

    # Impact extraction
    impact_match = re.search(
        r"(tạm đình chỉ thi công|đình chỉ|xử phạt|xung đột quy chuẩn|hết hiệu lực)",
        text,
        re.IGNORECASE,
    )
    if impact_match:
        impact = impact_match.group(0)

    return IntakeTaxonomy(
        subject=subject,
        action=action,
        impact=impact,
        scope=scope,
        time_timestamp=time_timestamp,
    )


def get_missing_intake_fields(intake: IntakeTaxonomy) -> list[str]:
    """Return a list of field names that are missing in the given taxonomy."""
    missing = []
    if not intake.subject:
        missing.append("subject")
    if not intake.action:
        missing.append("action")
    if not intake.impact:
        missing.append("impact")
    if not intake.scope:
        missing.append("scope")
    if not intake.time_timestamp:
        missing.append("time_timestamp")
    return missing


def generate_guided_interview_prompt(missing_fields: list[str]) -> str:
    """Generate a polite guided interview prompt asking the user for missing fields."""
    if not missing_fields:
        return "Tất cả 5 trục dữ kiện pháp lý đã đầy đủ."

    labels = [FIELD_DISPLAY_NAMES.get(f, f) for f in missing_fields]
    fields_str = ", ".join(labels)
    return f"Để đảm bảo tư vấn chính xác, vui lòng cung cấp thêm thông tin về các dữ kiện: {fields_str}."
