"""Chapter and appendix splitting utilities."""

from __future__ import annotations

import re
from pathlib import Path
from ccba_legal.formatter.metadata import extract_parent_metadata


def roman_to_decimal(r: str) -> int:
    """Convert Roman numeral string to decimal integer."""
    r = r.upper()
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50}
    val = 0
    for i in range(len(r)):
        if i > 0 and roman_map[r[i]] > roman_map[r[i - 1]]:
            val += roman_map[r[i]] - 2 * roman_map[r[i - 1]]
        else:
            val += roman_map[r[i]]
    return val


def split_concept_appendices(file_path: Path) -> list[str]:
    """Detect and split appendices from a markdown file, saving them in an appendices/ subdirectory."""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8")
    inherited = extract_parent_metadata(content)
    lines = content.splitlines()
    pattern = re.compile(r"^#*\s*(PHỤ LỤC\s+([IVXLCDM]+))\s*$", re.IGNORECASE)
    matches = []
    for idx, line in enumerate(lines):
        m = pattern.match(line.strip())
        if m:
            matches.append((idx, m.group(1), m.group(2)))
    if not matches:
        return []
    parent_slug = file_path.stem
    parent_dir = file_path.parent
    appendices_dir = parent_dir / "appendices"
    appendices_dir.mkdir(parents=True, exist_ok=True)
    main_body_lines = lines[: matches[0][0]]
    while main_body_lines and not main_body_lines[-1].strip():
        main_body_lines.pop()
    appendix_links = []
    for i, (idx, full_label, roman) in enumerate(matches):
        start_idx = idx
        end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(lines)
        app_lines = lines[start_idx:end_idx]
        app_lines.pop(0)
        title = ""
        for line in app_lines:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("(") and not cleaned.endswith(")"):
                title = cleaned.replace("#", "").strip()
                break
        if not title:
            title = f"{full_label}"
        dec_num = roman_to_decimal(roman)
        dec_str = f"{dec_num:02d}"
        app_filename = f"{parent_slug}-phu_luc_{dec_str}.md"
        app_path = appendices_dir / app_filename
        fm_lines = [
            "---",
            "type: Appendix",
            f'title: "{full_label} - {title}"',
            f'description: "Chi tiết {full_label} ban hành kèm theo {parent_slug.replace("_", " ").title()}"',
            f'parent_document: "../{file_path.name}"',
            'uniclass: "Fi_10_20"',
        ]
        for key, val in inherited.items():
            if isinstance(val, str):
                fm_lines.append(f'{key}: "{val}"')
            else:
                fm_lines.append(f"{key}: {val}")
        fm_lines.append("---")
        frontmatter = "\n".join(fm_lines) + f"\n\n# {full_label}\n\n"
        app_content = frontmatter + "\n".join(app_lines).strip() + "\n"
        app_path.write_text(app_content, encoding="utf-8")
        appendix_links.append(f"- [{full_label}: {title}](appendices/{app_filename})")
    new_parent_content = "\n".join(main_body_lines).strip() + "\n\n## DANH SÁCH PHỤ LỤC ĐÍNH KÈM\n\n" + "\n".join(appendix_links) + "\n"
    file_path.write_text(new_parent_content, encoding="utf-8")
    return [f"appendices/{parent_slug}-phu_luc_{f'{roman_to_decimal(m[2]):02d}'}.md" for m in matches]


def split_by_chapters(content: str, sections_dir: Path) -> None:
    """Split content by chapters and save them in the sections directory."""
    sections_dir.mkdir(parents=True, exist_ok=True)
    inherited = extract_parent_metadata(content)
    lines = content.splitlines()
    chuong_pattern = re.compile(r"^\s*(Chương|CHƯƠNG)\s+([IVXLCDM\d]+)", re.IGNORECASE)
    chapters = []
    curr_lines: list[str] = []
    curr_title = ""
    curr_num = 0
    preamble: list[str] = []
    in_preamble = True
    for line in lines:
        match = chuong_pattern.match(line)
        if match:
            in_preamble = False
            if curr_num > 0:
                chapters.append((curr_num, curr_title, curr_lines))
            elif preamble:
                chapters.append((0, "Preamble", preamble))
            curr_num += 1
            curr_title = line.strip()
            curr_lines = [line]
        else:
            if in_preamble:
                preamble.append(line)
            else:
                curr_lines.append(line)
    if curr_num > 0:
        chapters.append((curr_num, curr_title, curr_lines))
    elif preamble and not chapters:
        chapters.append((1, "Toàn văn", preamble))
    for num, title, clines in chapters:
        c_text = "\n".join(clines).strip()
        dest = sections_dir / f"chuong_{num:02d}.md"
        fm_lines = [
            "---",
            "type: Section",
            f'title: "{title}"',
            'parent_document: "../full_text.md"',
        ]
        for key, val in inherited.items():
            if isinstance(val, str):
                fm_lines.append(f'{key}: "{val}"')
            else:
                fm_lines.append(f"{key}: {val}")
        fm_lines.append("---")
        frontmatter = "\n".join(fm_lines) + "\n\n" + c_text + "\n"
        dest.write_text(frontmatter, encoding="utf-8")
