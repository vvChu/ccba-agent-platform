"""Two-way reply engine for CCBA Questionnaires.

Parses reply strings (e.g., '1A, 2B, 3C'), validates option ranges, guarantees
idempotent AST/markdown updates (unchecking prior choices), updates metadata to
RESOLVED, and records a Decision Log for seamless hand-off to /ccba-to-spec.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .models import QuestionnaireData, QuestionType
from .parser import parse_questionnaire_markdown


def parse_reply_string(reply_str: str) -> dict[int, tuple[str, str]]:
    """Parse a flexible reply string into a mapping of question_id -> (option_key, note).

    Supported patterns:
        - "1A, 2B, 3C"
        - "1:A, 2:B"
        - "1-A; 2-B"
        - "1=A, 2=C"
        - "1A, 2D (Phương án riêng TVTK)"

    Args:
        reply_str: Input response string from user/chat.

    Returns:
        Dictionary mapping int question id to (uppercase option key, client note).
    """
    token_regex = re.compile(
        r"(?:(?:Câu|Q)?\s*(\d+)\s*[:\-\=\.]?\s*([A-Za-z]))(?:\s*\((.*?)\))?",
        re.IGNORECASE,
    )
    results: dict[int, tuple[str, str]] = {}
    for match in token_regex.finditer(reply_str):
        qid = int(match.group(1))
        opt_key = match.group(2).upper()
        note = (match.group(3) or "").strip()
        results[qid] = (opt_key, note)
    return results


def apply_questionnaire_reply(
    source_file: str | Path,
    reply_str: str,
    resolved_by: str = "Chủ đầu tư / Ban QLDA",
    output_file: str | Path | None = None,
) -> Path:
    """Apply a reply string to a questionnaire markdown file.

    Validates that options exist, resets prior selections, marks new selections,
    updates status to RESOLVED, and appends a Decision Log.

    Args:
        source_file: Path to the input questionnaire markdown file.
        reply_str: Response string e.g. "1A, 2B, 3C".
        resolved_by: Name/Entity that approved the decision.
        output_file: Optional target path. If None, overwrites source_file.

    Returns:
        Path to the modified questionnaire file.
    """
    src_p = Path(source_file)
    if not src_p.is_file():
        raise FileNotFoundError(f"Source questionnaire file not found: {source_file}")

    target_p = Path(output_file) if output_file else src_p
    replies = parse_reply_string(reply_str)
    if not replies:
        raise ValueError(
            f"No valid question replies parsed from: '{reply_str}'. Expected format e.g. '1A, 2B'"
        )

    # 1. Parse and validate against models
    data: QuestionnaireData = parse_questionnaire_markdown(src_p)
    for qid, (opt_key, _) in replies.items():
        q = data.get_question(qid)
        if not q:
            raise ValueError(f"Question {qid} does not exist in questionnaire '{src_p.name}'")
        if q.q_type == QuestionType.HYPOTHESIS_MATRIX and q.options:
            if not q.get_option(opt_key):
                valid_keys = [o.key for o in q.options]
                raise ValueError(
                    f"Option '{opt_key}' is invalid for Question {qid}. Valid options: {valid_keys}"
                )

    # 2. Update lines in markdown
    raw_content = src_p.read_text(encoding="utf-8")
    lines = raw_content.splitlines()
    new_lines: list[str] = []

    current_qid: int | None = None
    q_header_regex = re.compile(
        r"^###\s+(?:(?:Câu\s*hỏi|Question|Q)?\s*(\d+)[\.:\-\s]+)?(.+)$", re.IGNORECASE
    )
    opt_line_regex = re.compile(
        r"^([-*]\s+\[)([ xX])(\]\s*(?:\*\*(?:Phương\s*án|Option|PA)?\s*([A-Za-z])(?:\s*\(.*?\))?[\*:]*|\[([A-Za-z])\]).*)$",
        re.IGNORECASE,
    )

    q_counter = 0
    for line in lines:
        stripped = line.strip()

        # Track question ID
        if q_match := q_header_regex.match(stripped):
            q_id_str = q_match.group(1)
            if q_id_str:
                current_qid = int(q_id_str)
            else:
                q_counter += 1
                current_qid = q_counter
            new_lines.append(line)
            continue

        # Check for option line inside a targeted question
        if current_qid and current_qid in replies:
            target_key, client_note = replies[current_qid]
            if opt_match := opt_line_regex.match(line):
                prefix = opt_match.group(1)  # e.g. "- ["
                opt_key1 = opt_match.group(4)
                opt_key2 = opt_match.group(5)
                this_opt_key = (opt_key1 or opt_key2 or "").upper()
                rest = opt_match.group(3)  # e.g. "] **Phương án A**: ..."

                if this_opt_key == target_key:
                    # Mark selected
                    new_line = f"{prefix}x{rest}"
                    new_lines.append(new_line)
                    if client_note:
                        new_lines.append(f"  * Ghi chú phê duyệt: {client_note}")
                else:
                    # Uncheck (idempotent single choice)
                    new_line = f"{prefix} {rest}"
                    new_lines.append(new_line)
                continue

        # Update metadata lines
        if "trạng thái" in stripped.lower() and "pending" in stripped.lower():
            line = re.sub(r"PENDING", "RESOLVED", line, flags=re.IGNORECASE)
        elif stripped.startswith("status:") and "pending" in stripped.lower():
            line = 'status: "RESOLVED"'

        new_lines.append(line)

    # 3. Add or update Decision Log section at bottom
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    decision_log_lines = [
        "",
        "## Nhật ký Quyết định (Decision Log)",
        f"- **Thời điểm chốt quyết định**: {now_str}",
        f"- **Đại diện phê duyệt**: {resolved_by}",
        f"- **Cú pháp phản hồi ghi nhận**: `{reply_str}`",
        "- **Kết quả thống nhất phương án**:",
    ]

    for qid in sorted(replies.keys()):
        opt_key, note = replies[qid]
        q = data.get_question(qid)
        q_title = q.title if q else f"Câu hỏi {qid}"
        opt_label = ""
        if q:
            opt = q.get_option(opt_key)
            if opt:
                opt_label = f" — {opt.label}"
        note_str = f" *(Ghi chú: {note})*" if note else ""
        decision_log_lines.append(
            f"  * **Câu {qid} ({q_title})**: Phương án **[{opt_key}]**{opt_label}{note_str}"
        )

    decision_log_lines.extend(
        [
            "",
            "> [!TIP]",
            "> **Bàn giao quy trình tiếp theo:** Toàn bộ quyết định đã được chốt. Có thể nạp trực tiếp kết quả này vào kỹ năng `/ccba-to-spec` để sinh PRD/Đặc tả kỹ thuật hoặc chuyển sang `/ccba-to-tickets` để phân rã nhiệm vụ phát triển.",
        ]
    )

    # Remove previous decision log if re-running
    joined_content = "\n".join(new_lines)
    if "## Nhật ký Quyết định (Decision Log)" in joined_content:
        joined_content = joined_content.split("## Nhật ký Quyết định (Decision Log)")[0].rstrip()

    final_content = joined_content + "\n" + "\n".join(decision_log_lines) + "\n"
    target_p.write_text(final_content, encoding="utf-8")
    return target_p
