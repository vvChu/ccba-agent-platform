"""Stateful Markdown parser for CCBA Questionnaires (v1.0 & v2.0).

Supports both legacy open-ended questions and v2.0 hypothesis matrix questions
with options A/B/C/D, trade-offs, metadata, and decision logs.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import (
    QuestionItem,
    QuestionnaireData,
    QuestionOption,
    QuestionType,
)


def _clean_text(text: str) -> str:
    """Trim text and remove markdown strong markers if wrapper."""
    t = text.strip()
    return t


def parse_questionnaire_markdown(source: str | Path) -> QuestionnaireData:
    """Parse Markdown content into a QuestionnaireData object.

    Args:
        source: Markdown text string or Path to a .md file.

    Returns:
        QuestionnaireData instance populated from the markdown source.
    """
    if isinstance(source, Path):
        content = source.read_text(encoding="utf-8")
    elif len(source) < 1024 and ("\n" not in source) and Path(source).is_file():
        content = Path(source).read_text(encoding="utf-8")
    else:
        content = str(source)

    lines = content.splitlines()
    data = QuestionnaireData()
    metadata = data.metadata

    # 1. Parse Frontmatter if present
    line_idx = 0
    if lines and lines[0].strip() == "---":
        line_idx = 1
        fm_lines: list[str] = []
        while line_idx < len(lines) and lines[line_idx].strip() != "---":
            fm_lines.append(lines[line_idx])
            line_idx += 1
        if line_idx < len(lines):
            line_idx += 1  # Skip closing ---
        # Parse simple frontmatter keys
        for fml in fm_lines:
            if ":" in fml:
                k, v = fml.split(":", 1)
                k = k.strip().lower()
                v = v.strip().strip('"').strip("'")
                if k == "title":
                    metadata.title = v
                elif k in ("track", "category"):
                    metadata.track = v
                elif k in ("status", "state"):
                    metadata.status = v.upper()
                elif k == "doc_code":
                    metadata.doc_code = v

    current_section = ""
    current_question: QuestionItem | None = None
    current_option: QuestionOption | None = None
    q_counter = 0

    section_regex = re.compile(r"^##\s+(.+)$")
    h1_regex = re.compile(r"^#\s+(.+)$")
    q_header_regex = re.compile(
        r"^###\s+(?:(?:Câu\s*hỏi|Question|Q)?\s*(\d+)[\.:\-\s]+)?(.+)$", re.IGNORECASE
    )
    # Match options: - [ ] **Phương án A**: text or - [x] **Phương án A (⭐ Khuyến nghị)**: text or - [ ] [A] text
    opt_regex = re.compile(
        r"^[-*]\s+\[([ xX])\]\s*(?:\*\*(?:Phương\s*án|Option|PA)?\s*([A-Za-z])(?:\s*\((.*?)\))?[\*:]*|\[([A-Za-z])\])\s*(.*)$",
        re.IGNORECASE,
    )
    tradeoff_regex = re.compile(
        r"^\s+(?:[-*]\s+(?:Trade-off|Đánh\s*đổi|Tradeoff|Ưu/Nhược\s*điểm)[\s:]*|↳\s*)(.+)$",
        re.IGNORECASE,
    )
    why_regex = re.compile(
        r"^(?:>\s*)?(?:\*{1,2}|_{1,2})?\s*(?:Tại\s*sao(?:\s*điều\s*này)?\s*quan\s*trọng|Tại\s*sao\s*cần\s*quyết\s*định|Bối\s*cảnh|Why\s*it\s*matters)[\s:\*_-]+(.*)$",
        re.IGNORECASE,
    )
    open_box_regex = re.compile(
        r"^>\s*\[(?:Nhập\s*câu\s*trả\s*lời\s*tại\s*đây|Nhập\s*câu\s*trả\s*lời|Câu\s*trả\s*lời|Reply\s*here)\]\s*$",
        re.IGNORECASE,
    )

    while line_idx < len(lines):
        line = lines[line_idx]
        stripped = line.strip()

        # Handle H1 title if not set
        if h1_match := h1_regex.match(stripped):
            raw_title = h1_match.group(1).strip()
            # Clean up tags like [PHIẾU LẤY Ý KIẾN]
            metadata.title = raw_title
            line_idx += 1
            continue

        # Check inline metadata lines (e.g. **Mục đích:** ..., **Người gửi:** ...)
        if stripped.startswith("**") and (":**" in stripped or "**:" in stripped):
            # Parse pairs like: **Mục đích:** Lý do... — **Người gửi:** CCBA
            parts = re.split(r"\s*[—–-]\s*(?=\*\*)", stripped)
            matched_any = False
            for part in parts:
                m = re.match(r"^\*\*([^*:]+)(?::\*\*|\*\*:)[\s]*(.*)$", part.strip())
                if m:
                    matched_any = True
                    key = m.group(1).strip().lower()
                    val = m.group(2).strip()
                    if "mục đích" in key or "purpose" in key:
                        metadata.purpose = val
                    elif "gửi" in key or "sender" in key:
                        metadata.sender = val
                    elif "nhận" in key or "recipient" in key:
                        metadata.recipient = val
                    elif "dự án" in key or "project" in key:
                        metadata.project_name = val
                    elif "mã" in key or "code" in key:
                        metadata.doc_code = val
                    elif "trạng thái" in key or "status" in key:
                        metadata.status = val.upper()
                    elif "thời hạn" in key or "deadline" in key:
                        metadata.deadline = val
                    elif "phân luồng" in key or "track" in key:
                        metadata.track = val.lower()
                    elif "ngày chốt" in key or "resolved" in key:
                        metadata.resolved_at = val
                    elif "phê duyệt bởi" in key or "chốt bởi" in key:
                        metadata.resolved_by = val
            if matched_any:
                line_idx += 1
                continue

        # Handle H2 sections
        if sec_match := section_regex.match(stripped):
            sec_title = sec_match.group(1).strip()
            sec_lower = sec_title.lower()

            if "ngữ cảnh" in sec_lower or "context" in sec_lower:
                current_section = "context"
            elif "hướng dẫn" in sec_lower or "instruction" in sec_lower:
                current_section = "instructions"
            elif "ý kiến khác" in sec_lower or "anything else" in sec_lower:
                current_section = "additional_notes"
            elif "nhật ký quyết định" in sec_lower or "decision log" in sec_lower:
                current_section = "decision_log"
            else:
                # Could be a question group or topic section
                current_section = f"topic:{sec_title}"

            current_question = None
            current_option = None
            line_idx += 1
            continue

        # Handle H3 question headers
        if q_match := q_header_regex.match(stripped):
            q_id_str = q_match.group(1)
            q_text = q_match.group(2).strip()
            if q_id_str:
                qid = int(q_id_str)
            else:
                q_counter += 1
                qid = q_counter

            current_question = QuestionItem(
                id=qid,
                title=q_text,
                q_type=QuestionType.HYPOTHESIS_MATRIX,  # default, revised if open
            )
            data.questions.append(current_question)
            current_option = None
            line_idx += 1
            continue

        # If we are in a question block
        if current_question:
            # Check for Why It Matters
            if why_match := why_regex.match(stripped):
                current_question.why_it_matters = why_match.group(1).strip().strip("*_")
                line_idx += 1
                continue

            # Check for Option line
            if opt_match := opt_regex.match(stripped):
                checked = opt_match.group(1).lower() == "x"
                opt_key1 = opt_match.group(2)
                tag_notes = opt_match.group(3) or ""
                opt_key2 = opt_match.group(4)
                label_text = opt_match.group(5) or ""

                opt_key = (opt_key1 or opt_key2 or "A").upper()
                is_rec = "⭐" in tag_notes or "khuyến nghị" in tag_notes.lower() or "⭐" in label_text

                clean_label = label_text.strip()
                # Remove star or tag from label if repeated
                clean_label = re.sub(r"\(⭐.*?\)", "", clean_label).strip()

                current_option = QuestionOption(
                    key=opt_key,
                    label=clean_label,
                    is_recommended=is_rec,
                    is_selected=checked,
                )
                current_question.options.append(current_option)
                line_idx += 1
                continue

            # Check for Trade-off indented line
            if current_option and (to_match := tradeoff_regex.match(line)):
                current_option.trade_off = to_match.group(1).strip()
                line_idx += 1
                continue

            # Check for Open Question placeholder (v1.0 backward compatibility)
            if open_box_regex.match(stripped):
                current_question.q_type = QuestionType.OPEN_ENDED
                line_idx += 1
                continue

            # Check for open question reply text
            if current_question.q_type == QuestionType.OPEN_ENDED and stripped.startswith(">"):
                quote_content = stripped.lstrip("> ").strip()
                if quote_content and not open_box_regex.match(stripped):
                    if current_question.freeform_reply:
                        current_question.freeform_reply += "\n" + quote_content
                    else:
                        current_question.freeform_reply = quote_content
                line_idx += 1
                continue

        # If not inside a specific question, append to sections
        if current_section == "context":
            if stripped:
                data.context += (data.context and "\n" or "") + stripped
        elif current_section == "instructions":
            if stripped:
                data.instructions += (data.instructions and "\n" or "") + stripped
        elif current_section == "additional_notes":
            if stripped:
                data.additional_notes += (data.additional_notes and "\n" or "") + stripped

        line_idx += 1

    # Post-processing: If a question has no options, classify as OPEN_ENDED
    for q in data.questions:
        if not q.options:
            q.q_type = QuestionType.OPEN_ENDED

    # Generate default doc_code if missing
    if not metadata.doc_code:
        metadata.doc_code = f"CCBA-QST-{abs(hash(metadata.title)) % 10000:04d}"

    return data
