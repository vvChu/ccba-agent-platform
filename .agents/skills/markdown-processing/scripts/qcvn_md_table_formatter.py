"""QCVN Markdown Table Standardizer Engine.

Scans QCVN markdown documents and replaces broken/multiline table blocks
with 100% clean, beautifully structured 2D GFM Markdown Pipe Tables (| Col 1 | Col 2 |).
"""

import re
from pathlib import Path


def format_all_qcvn_md_tables(md_path: Path) -> int:
    """Scan and convert all multiline/broken table blocks in md_path to 2D GFM Pipe Tables."""
    if not md_path.exists():
        return 0

    content = md_path.read_text(encoding="utf-8")

    # Regular expression matching Bảng X header blocks
    table_block_regex = re.compile(
        r"(<a id=\"[^\"]+\"></a>\n)?([#*]+)?\s*(Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^\n\*\#]+))([#*]*|\n)?"
        r"(.*?)(?=\n<a id=\"muc-|\n### |\n# |\n(?:\#|\*)*\s*Bảng|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    formatted_count = 0

    def replace_table_block(match: re.Match) -> str:
        nonlocal formatted_count
        full_match_text = match.group(0)
        table_num = match.group(4)
        table_title_text = match.group(5).strip("*\n# ")
        table_title = f"Bảng {table_num} - {table_title_text}"
        table_anchor = f"bang-{table_num.lower().replace('.', '-')}"
        body_text = match.group(7)

        # Clean body text lines
        raw_lines = body_text.splitlines()
        clean_tokens: list[str] = []
        footnotes: list[str] = []

        for line in raw_lines:
            line_str = line.strip()
            # Remove inline anchors
            clean_str = re.sub(r"<a id=\"[^\"]+\"></a>", "", line_str)
            clean_str = re.sub(r"^[#*\s|]+", "", clean_str).strip(" |")

            if not clean_str or clean_str == "---":
                continue

            if re.match(r"^\d+\)\s+", clean_str) or clean_str.startswith("CHÚ THÍCH"):
                footnotes.append(clean_str)
                continue

            if "\t" in clean_str:
                parts = [p.strip(" |") for p in clean_str.split("\t") if p.strip()]
                clean_tokens.extend(parts)
            else:
                clean_tokens.append(clean_str)

        if len(clean_tokens) < 2:
            return full_match_text

        # Find header boundary vs data rows
        header_end = 1
        for tok_idx, tok in enumerate(clean_tokens[1:], 1):
            if re.match(r"^\d+[\.\)]?\s*", tok) or re.search(r"\b(REI|EI|R|E|P|F\d)\s*\d*", tok):
                header_end = tok_idx
                break

        cols_count = max(1, header_end)
        header_row = clean_tokens[:cols_count]
        data_tokens = clean_tokens[cols_count:]

        data_rows: list[list[str]] = []
        for chunk_idx in range(0, len(data_tokens), cols_count):
            chunk = data_tokens[chunk_idx : chunk_idx + cols_count]
            if any(chunk):
                if len(chunk) < cols_count:
                    chunk.extend([""] * (cols_count - len(chunk)))
                data_rows.append(chunk)

        if not data_rows:
            return full_match_text

        # Construct clean 2D GFM Markdown Pipe Table
        md_lines = [
            f'<a id="{table_anchor}"></a>',
            f"### {table_title}\n",
            "| " + " | ".join(header_row) + " |",
            "| " + " | ".join(["---"] * cols_count) + " |",
        ]
        for row in data_rows:
            md_lines.append("| " + " | ".join(row) + " |")

        if footnotes:
            md_lines.append("\n" + "\n".join(f"_{fn}_" for fn in footnotes))

        md_lines.append("\n")
        formatted_count += 1
        return "\n".join(md_lines)

    new_content = table_block_regex.sub(replace_table_block, content)
    md_path.write_text(new_content, encoding="utf-8")
    return formatted_count
