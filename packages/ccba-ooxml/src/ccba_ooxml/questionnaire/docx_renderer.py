"""Word (.docx) renderer for CCBA Questionnaires.

Generates formal CCBA Decision & Technical Coordination Questionnaires with
metadata grid, hypotheses matrix tables, Unicode checkboxes, and 3-party sign-off blocks.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

from .models import QuestionnaireData, QuestionType

NAVY_BLUE = RGBColor(0, 51, 102)  # #003366 CCBA Brand Blue
SLATE_GRAY = RGBColor(100, 116, 139)
MUTED_DARK = RGBColor(30, 41, 59)


def set_cell_background(cell: docx.table._Cell, fill_hex: str) -> None:
    """Set the background color (shading) of a table cell."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def set_table_borders(table: docx.table.Table, color: str = "CBD5E1") -> None:
    """Apply elegant light borders to a table."""
    tbl_pr = table._tbl.tblPr
    borders_xml = f"""
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
    </w:tblBorders>
    """
    tbl_pr.append(parse_xml(borders_xml))


def render_questionnaire_docx(data: QuestionnaireData, output_path: str | Path) -> Path:
    """Render a QuestionnaireData object into a formatted Word (.docx) document.

    Args:
        data: Parsed QuestionnaireData instance.
        output_path: Target path for the generated .docx file.

    Returns:
        Path to the saved .docx document.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document()

    # 1. Page Margins (A4 Standard 0.75 in)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    meta = data.metadata

    # 2. Document Header
    p_hdr = doc.add_paragraph()
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_hdr.add_run(meta.title.upper() + "\n")
    r_title.bold = True
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = NAVY_BLUE

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    status_label = f"Trạng thái: {meta.status}"
    if meta.status == "RESOLVED" and meta.resolved_at:
        status_label += f" ({meta.resolved_at})"
    track_label = meta.track.upper()
    r_sub = p_sub.add_run(f"Mã phiếu: {meta.doc_code} | Phân luồng: {track_label} | {status_label}")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(9.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = SLATE_GRAY

    # 3. Metadata Table (Project & Context Grid)
    meta_table = doc.add_table(rows=3, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, "E2E8F0")

    meta_rows = [
        (
            "Dự án / Hạng mục:",
            meta.project_name or "(Chưa xác định)",
            "Bên phát hành:",
            meta.sender or "CCBA BIM/MEP",
        ),
        (
            "Mục đích lấy ý kiến:",
            meta.purpose or "Thống nhất phương án kỹ thuật",
            "Bên tiếp nhận:",
            meta.recipient or "Chủ đầu tư / TVTK",
        ),
        (
            "Thời hạn phản hồi:",
            meta.deadline or "Trong vòng 03 ngày làm việc",
            "Quyết định phê duyệt:",
            meta.resolved_by or "(Đang chờ phản hồi)",
        ),
    ]

    for row_idx, (k1, v1, k2, v2) in enumerate(meta_rows):
        row = meta_table.rows[row_idx]
        c0, c1 = row.cells[0], row.cells[1]

        p0 = c0.paragraphs[0]
        r_k1 = p0.add_run(f"{k1} ")
        r_k1.bold = True
        r_k1.font.size = Pt(9.5)
        p0.add_run(v1).font.size = Pt(9.5)

        p1 = c1.paragraphs[0]
        r_k2 = p1.add_run(f"{k2} ")
        r_k2.bold = True
        r_k2.font.size = Pt(9.5)
        p1.add_run(v2).font.size = Pt(9.5)

        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "F8FAFC")

    doc.add_paragraph()  # Vertical spacing

    # 4. Context & Instructions if present
    if data.context:
        p_ctx = doc.add_paragraph()
        r_ctx_title = p_ctx.add_run("Bối cảnh chung: ")
        r_ctx_title.bold = True
        r_ctx_title.font.color.rgb = NAVY_BLUE
        p_ctx.add_run(data.context).font.size = Pt(9.5)

    if data.instructions:
        p_ins = doc.add_paragraph()
        r_ins_title = p_ins.add_run("Hướng dẫn phản hồi: ")
        r_ins_title.bold = True
        r_ins_title.font.color.rgb = NAVY_BLUE
        p_ins.add_run(data.instructions).font.size = Pt(9.5)

    # 5. Questions & Hypotheses Matrix Table
    q_table = doc.add_table(rows=1, cols=3)
    q_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(q_table, "CBD5E1")

    # Header Row
    hdr_cells = q_table.rows[0].cells
    hdr_cells[0].text = "STT & Vấn đề kỹ thuật"
    hdr_cells[1].text = "Phương án đề xuất (Hypotheses Matrix)"
    hdr_cells[2].text = "Ý kiến chốt / Phê duyệt"

    col_widths = [Inches(2.2), Inches(3.6), Inches(1.5)]
    for c_idx, c in enumerate(hdr_cells):
        c.width = col_widths[c_idx]
        set_cell_background(c, "003366")
        for p in c.paragraphs:
            for r in p.runs:
                r.font.name = "Segoe UI"
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.bold = True
                r.font.size = Pt(10)

    # Rows for each question
    for q in data.questions:
        row_cells = q_table.add_row().cells
        for c_idx, c in enumerate(row_cells):
            c.width = col_widths[c_idx]

        # Column 1: Question title & Why it matters
        p_q = row_cells[0].paragraphs[0]
        r_qid = p_q.add_run(f"Câu {q.id}: {q.title}\n")
        r_qid.bold = True
        r_qid.font.size = Pt(10)
        r_qid.font.color.rgb = MUTED_DARK

        if q.why_it_matters:
            r_why = p_q.add_run(f"📌 Bối cảnh: {q.why_it_matters}")
            r_why.font.size = Pt(8.5)
            r_why.font.color.rgb = SLATE_GRAY

        # Column 2: Options or Open-ended prompt
        p_opts = row_cells[1].paragraphs[0]
        if q.q_type == QuestionType.OPEN_ENDED or not q.options:
            r_open = p_opts.add_run("☐ Câu hỏi mở / Ghi ý kiến thảo luận:\n")
            r_open.bold = True
            r_open.font.size = Pt(9.5)
            if q.freeform_reply:
                p_opts.add_run(f"{q.freeform_reply}\n").font.size = Pt(9)
            else:
                p_opts.add_run(
                    "\n\n......................................................................................\n"
                ).font.color.rgb = SLATE_GRAY
        else:
            for opt in q.options:
                box = "☑" if opt.is_selected else "☐"
                star = " (⭐ Đề xuất CCBA)" if opt.is_recommended else ""
                r_opt = p_opts.add_run(f"{box} [{opt.key}] {opt.label}{star}\n")
                r_opt.font.size = Pt(9.5)
                r_opt.bold = opt.is_recommended or opt.is_selected
                if opt.is_selected:
                    r_opt.font.color.rgb = NAVY_BLUE

                if opt.trade_off:
                    r_to = p_opts.add_run(f"   ↳ {opt.trade_off}\n")
                    r_to.font.size = Pt(8.5)
                    r_to.font.color.rgb = SLATE_GRAY

        # Column 3: Client Feedback
        p_fb = row_cells[2].paragraphs[0]
        selected_key = next((opt.key for opt in q.options if opt.is_selected), None)
        if selected_key:
            r_sel = p_fb.add_run(f"☑ Chốt PA [{selected_key}]\n")
            r_sel.bold = True
            r_sel.font.size = Pt(9.5)
            r_sel.font.color.rgb = NAVY_BLUE
            if q.client_note:
                p_fb.add_run(f"Ghi chú: {q.client_note}").font.size = Pt(8.5)
        else:
            p_fb.add_run("☐ Đồng ý PA đề xuất\n☐ PA khác:\n............").font.size = Pt(9)

    doc.add_paragraph()  # Vertical spacing

    # 6. Additional Notes / Ý kiến khác
    if data.additional_notes:
        p_notes = doc.add_paragraph()
        r_n_title = p_notes.add_run("Ý kiến bổ sung khác:\n")
        r_n_title.bold = True
        r_n_title.font.color.rgb = NAVY_BLUE
        p_notes.add_run(data.additional_notes).font.size = Pt(9.5)
        doc.add_paragraph()

    # 7. Sign-off / Approval Block (3 parties)
    p_sign_title = doc.add_paragraph()
    r_st = p_sign_title.add_run("XÁC NHẬN VÀ PHÊ DUYỆT CÁC BÊN:")
    r_st.bold = True
    r_st.font.size = Pt(10)
    r_st.font.color.rgb = NAVY_BLUE

    sign_table = doc.add_table(rows=2, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(sign_table, "E2E8F0")

    sign_roles = [
        "ĐẠI DIỆN CCBA\n(Đơn vị tư vấn đề xuất)",
        "ĐƠN VỊ TƯ VẤN THIẾT KẾ\n(Xem xét và phản hồi)",
        "CHỦ ĐẦU TƯ / BQL DỰ ÁN\n(Phê duyệt chính thức)",
    ]

    for idx, role in enumerate(sign_roles):
        c_hdr = sign_table.rows[0].cells[idx]
        p_h = c_hdr.paragraphs[0]
        p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_h.add_run(role)
        r.bold = True
        r.font.size = Pt(9)
        set_cell_background(c_hdr, "F8FAFC")

        c_body = sign_table.rows[1].cells[idx]
        p_b = c_body.paragraphs[0]
        p_b.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_b.add_run("\n\n\n\nNgày ... tháng ... năm 2026\n(Ký và ghi rõ họ tên)").font.size = Pt(
            8.5
        )

    doc.save(str(out_p))
    return out_p
