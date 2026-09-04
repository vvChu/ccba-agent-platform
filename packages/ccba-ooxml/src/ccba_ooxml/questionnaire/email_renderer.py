"""HTML Email table renderer for CCBA Questionnaires.

Generates an inline-styled HTML table ready for pasting into Outlook, Gmail,
and corporate email clients.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import html

from .models import QuestionnaireData, QuestionType


def render_email_table(data: QuestionnaireData) -> str:
    """Render questionnaire as an email-compatible HTML table with inline styles.

    Args:
        data: Parsed QuestionnaireData instance.

    Returns:
        HTML table string suitable for email body.
    """
    meta = data.metadata
    title_esc = html.escape(meta.title)
    project_esc = html.escape(meta.project_name or "(Dự án)")
    recipient_esc = html.escape(meta.recipient or "Quý Đối tác")

    rows_html: list[str] = []
    for q in data.questions:
        q_title_esc = html.escape(q.title)
        why_html = ""
        if q.why_it_matters:
            why_html = f'<div style="font-size:12px;color:#64748b;margin-top:4px;">📌 {html.escape(q.why_it_matters)}</div>'

        if q.q_type == QuestionType.OPEN_ENDED or not q.options:
            opts_html = '<div style="font-style:italic;color:#64748b;">(Câu hỏi thảo luận mở — Quý đối tác vui lòng cho ý kiến)</div>'
        else:
            opts_items = []
            for opt in q.options:
                k_esc = html.escape(opt.key)
                l_esc = html.escape(opt.label)
                star = ' <span style="color:#0284c7;font-weight:bold;">(⭐ Khuyến nghị CCBA)</span>' if opt.is_recommended else ''
                to_html = f'<div style="font-size:12px;color:#64748b;">↳ {html.escape(opt.trade_off)}</div>' if opt.trade_off else ''
                opts_items.append(
                    f'<li style="margin-bottom:6px;">'
                    f'<b>[{k_esc}]</b> {l_esc}{star}'
                    f'{to_html}'
                    f'</li>'
                )
            opts_html = f'<ul style="margin:0;padding-left:18px;">{"".join(opts_items)}</ul>'

        rows_html.append(f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 12px; vertical-align: top; width: 35%; font-weight: bold; color: #1e293b;">
            {q.id}. {q_title_esc}
            {why_html}
          </td>
          <td style="padding: 12px; vertical-align: top;">
            {opts_html}
          </td>
        </tr>
        """)

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; color: #1e293b; max-width: 720px; line-height: 1.5;">
      <h3 style="color: #003366; margin-bottom: 4px; border-bottom: 2px solid #003366; padding-bottom: 6px;">
        PHIẾU LẤY Ý KIẾN THIẾT KẾ: {title_esc}
      </h3>
      <p style="font-size: 13px; color: #475569; margin-top: 6px; margin-bottom: 14px;">
        <b>Dự án:</b> {project_esc} | <b>Kính gửi:</b> {recipient_esc}
      </p>
      <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1;">
        <thead>
          <tr style="background-color: #003366; color: #ffffff;">
            <th style="padding: 10px; text-align: left; font-size: 13px;">Vấn đề kỹ thuật</th>
            <th style="padding: 10px; text-align: left; font-size: 13px;">Các phương án lựa chọn (Hypotheses Matrix)</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
      <div style="margin-top: 14px; padding: 12px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; font-size: 13px;">
        👉 <b>Cách thức phản hồi:</b> Quý đối tác có thể trả lời trực tiếp email này với cú pháp ngắn gọn, ví dụ: <code>1A, 2B, 3C</code> hoặc đính kèm văn bản xác nhận.
      </div>
    </div>
    """
