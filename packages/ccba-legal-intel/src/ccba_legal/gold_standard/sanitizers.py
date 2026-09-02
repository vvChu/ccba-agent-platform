"""Text and table sanitization utilities."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def strip_existing_anchors(text: str) -> str:
    """Strip existing inline anchors to make pipeline idempotent."""
    return re.sub(r'<a\s+(?:id|name)="[^"]+"></a>\s*', "", text)


def normalize_tvpl_formatting(text: str) -> str:
    """Normalize line wrapping in raw TVPL text."""
    text = re.sub(r"Điều\s*[\r\n]+\s*(\d+\.)", r"Điều \1", text, flags=re.IGNORECASE)
    text = re.sub(r"Chương\s*[\r\n]+\s*([IVXLCDM]+)", r"Chương \1", text, flags=re.IGNORECASE)
    text = re.sub(r"Mục\s*[\r\n]+\s*(\d+\.)", r"Mục \1", text, flags=re.IGNORECASE)
    return text


def clean_html_tables(text: str) -> str:
    """Convert HTML <table> blocks into clean Markdown tables."""
    if "<table" not in text.lower():
        return text

    def _replace_table(match: re.Match) -> str:
        html = match.group(0)
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr")
        if not rows:
            return ""
        table_matrix: list[list[str]] = []
        for tr in rows:
            cols = tr.find_all(["td", "th"])
            row_data = [re.sub(r"\s+", " ", col.get_text(strip=True)) for col in cols]
            if any(row_data):
                table_matrix.append(row_data)
        if not table_matrix:
            return ""
        max_cols = max(len(r) for r in table_matrix)
        md_lines = []
        header = table_matrix[0] + [""] * (max_cols - len(table_matrix[0]))
        md_lines.append("| " + " | ".join(header) + " |")
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        for row in table_matrix[1:]:
            padded = row + [""] * (max_cols - len(row))
            md_lines.append("| " + " | ".join(padded) + " |")
        return "\n" + "\n".join(md_lines) + "\n"

    pattern = re.compile(r"<table.*?>.*?</table>", re.DOTALL | re.IGNORECASE)
    return pattern.sub(_replace_table, text)


def clean_table_footnotes_and_superscripts(text: str) -> str:
    """Untrap footnotes from table rows and format in-cell markers as <sup>X)</sup>."""
    lines = text.splitlines()
    new_lines: list[str] = []
    in_table = False
    table_lines: list[str] = []

    def _process_table(t_lines: list[str]) -> list[str]:
        extracted_footnotes: list[str] = []
        cleaned_t_lines: list[str] = []
        for line in t_lines:
            trapped_match = re.search(
                r"\|\s*(_[1-9]\)|_CHÚ THÍCH|_GHI CHÚ|_Đối với|_Ghi chú|_Không yêu cầu|_Nếu không|_Cho phép)(.*?)\|\s*$",
                line,
            )
            if trapped_match:
                note_text = trapped_match.group(1) + trapped_match.group(2)
                line = line[: trapped_match.start()] + "|"
                clean_note = note_text.strip("_ ").strip()
                note_parts = re.split(r"(?<=\.)\s+(?=[1-9]\))", clean_note)
                prefixes = ("1)", "2)", "3)", "4)")
                if not note_parts or (len(note_parts) == 1 and not clean_note.startswith(prefixes)):
                    if not clean_note.startswith(prefixes):
                        clean_note = "1) " + clean_note
                    note_parts = [clean_note]
                for part in note_parts:
                    p = part.strip()
                    if p:
                        extracted_footnotes.append(p)
                if line.replace("|", "").strip() == "":
                    continue

            def _superscript_marker(m: re.Match) -> str:
                return f"<sup>{m.group(1)}</sup>"

            line = re.sub(r"\s*([1-9]\))(?=\s*(?:\||$))", _superscript_marker, line)
            cleaned_t_lines.append(line)
        res = cleaned_t_lines
        if extracted_footnotes:
            res.append("")
            res.append("_GHI CHÚ CHỈ SỐ PHỤ:_")
            for fn in extracted_footnotes:
                fn_clean = fn.strip("_* ")
                m_fn = re.match(r"^(\d+\))\s*(.*)", fn_clean)
                if m_fn:
                    res.append(f"- **{m_fn.group(1)}** {m_fn.group(2)}")
                else:
                    res.append(f"- {fn_clean}")
            res.append("")
        return res

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(line)
        else:
            if in_table:
                new_lines.extend(_process_table(table_lines))
                table_lines = []
                in_table = False
            new_lines.append(line)
    if in_table:
        new_lines.extend(_process_table(table_lines))
    return "\n".join(new_lines)


def normalize_notes_and_lists(text: str) -> str:
    """Normalize notes structure, deduplicate headers, and format lists cleanly."""
    lines = text.splitlines()
    cleaned_bullet_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^([-*]\s+)+", stripped):
            stripped = re.sub(r"^([-*]\s+)+", "- ", stripped)
        cleaned_bullet_lines.append(stripped if not line.startswith("  ") else line)
    text = "\n".join(cleaned_bullet_lines)
    text = re.sub(
        r'(####\s*<a id="muc-1-4-9"[^\n]+\n+Chiều cao PCCC của nhà[^\n]+\n+)\s*(Bằng khoảng cách lớn nhất[^\n]+)\n+\s*(Bằng một nửa tổng khoảng cách[^\n]+)',
        r"\1- \2\n\n- \3",
        text,
    )
    text = re.sub(
        r"(_?CHÚ THÍCH:\s*Các yếu tố nguy hiểm cháy[^\n]+)\n+\s*[-*]?\s*2\.\s*(luồng nhiệt[^\n]+)",
        r"_CHÚ THÍCH: Các yếu tố nguy hiểm cháy: 1) ngọn lửa và tia lửa, 2) \2_",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"(?m)^\s*_CHÚ THÍCH:_\s*\n+(?=\s*-\s+\*\*CHÚ THÍCH\s+[2-9])", "", text)
    text = re.sub(
        r"(\n-\s+\*\*CHÚ THÍCH\s+\d+:?\*\*[^\n]+\n+)\s*_CHÚ THÍCH:_\n+(?=-\s+\*\*CHÚ THÍCH)",
        r"\1",
        text,
    )

    def _fix_codes(match: re.Match) -> str:
        return f"- {match.group(1).strip()}"

    text = re.sub(
        r"(?m)^(?!\s*[-*])\s*((?:LT[1-4]|Ch[1-4]|BC[1-3]|SK[1-3]|ĐT[1-4]|CV[0-5]|K[0-3])\s*\([^\n]+)",
        _fix_codes,
        text,
    )
    lines = text.splitlines()
    processed_lines: list[str] = []
    in_note = False
    for l_item in lines:
        st = l_item.strip()
        if st == "_CHÚ THÍCH:_":
            in_note = True
            processed_lines.append(l_item)
            continue
        elif st.startswith(("#", "<a id=", "|", ">", "```")):
            in_note = False
            processed_lines.append(l_item)
            continue
        if in_note:
            m_let = re.match(r"^([a-z]\)\s+.*)", st)
            if m_let:
                processed_lines.append(f"  {m_let.group(1)}")
                continue
            m_sub_b = re.match(r"^\s*-\s+([a-z]\)\s+.*)", st)
            if m_sub_b:
                processed_lines.append(f"  {m_sub_b.group(1)}")
                continue
        else:
            m_main_let = re.match(r"^[-*]\s+([a-z]\)\s+.*)", st)
            if m_main_let:
                processed_lines.append(m_main_let.group(1))
                continue
        processed_lines.append(l_item)
    text = "\n".join(processed_lines)
    return re.sub(r"\n{3,}", "\n\n", text)
