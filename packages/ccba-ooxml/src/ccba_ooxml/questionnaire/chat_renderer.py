"""Micro-chat snippet generator for CCBA Questionnaires.

Generates concise, mobile-optimized snippets (<15 lines) suitable for
messaging apps (Zalo, Microsoft Teams, Viber, Slack).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from .models import QuestionnaireData, QuestionType


def render_chat_snippet(data: QuestionnaireData) -> str:
    """Render questionnaire as a compact chat snippet (<15 lines).

    Args:
        data: Parsed QuestionnaireData instance.

    Returns:
        Formatted chat string.
    """
    meta = data.metadata
    lines: list[str] = [
        f"📋 *[PHIẾU LẤY Ý KIẾN THIẾT KẾ]* {meta.title}",
        f"🏢 *Dự án:* {meta.project_name or 'Dự án'} | *Kính gửi:* {meta.recipient or 'Đối tác'}",
        "─────────────────────────",
    ]

    for q in data.questions[:5]:  # Limit to top 5 questions to keep under 15 lines
        if q.q_type == QuestionType.OPEN_ENDED or not q.options:
            lines.append(f"*{q.id}. {q.title[:45]}*")
            lines.append("   ↳ [Câu hỏi mở — Vui lòng gửi phản hồi trực tiếp]")
        else:
            opt_summaries = []
            for opt in q.options:
                star = "⭐" if opt.is_recommended else ""
                opt_summaries.append(f"[{opt.key}]{star} {opt.label[:20]}")
            lines.append(f"*{q.id}. {q.title[:45]}*")
            lines.append("   " + " | ".join(opt_summaries))

    lines.append("─────────────────────────")
    lines.append("👉 *Phản hồi nhanh:* Trả lời tin nhắn này với cú pháp ví dụ: `1A, 2B, 3C` để xác nhận.")
    return "\n".join(lines)
