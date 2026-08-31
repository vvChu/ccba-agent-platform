"""Metadata extraction and inline anchor injection utilities."""

from __future__ import annotations

import re
from typing import Any

import yaml


def extract_parent_metadata(content: str) -> dict[str, Any]:
    """Extract required metadata fields from frontmatter in parent content."""
    parent_fm: dict[str, str] = {}
    if content.strip().startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                parent_fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
    inherited = {}
    for key in ["resource", "status", "document_number", "timestamp"]:
        if key in parent_fm:
            inherited[key] = parent_fm[key]
    return inherited


def inject_anchors(text: str) -> str:
    """Detect legal hierarchies and inject hidden HTML anchor tags at matching lines."""
    lines = text.splitlines()
    output_lines = []
    current_dieu = None
    current_khoan = None
    chuong_pattern = re.compile(r"^\s*(Chương|CHƯƠNG)\s+([IVXLCDM\d]+)", re.IGNORECASE)
    muc_pattern = re.compile(r"^\s*(Mục|MỤC)\s+(\d+)", re.IGNORECASE)
    dieu_pattern = re.compile(r"^\s*(Điều|ĐIỀU)\s+(\d+)", re.IGNORECASE)
    khoan_pattern = re.compile(r"^(\s*)(\d+)[\.\)](\s+.*|\s*)$")
    diem_pattern = re.compile(r"^(\s*)([a-zđĐ])[\.\)](\s+.*|\s*)$", re.IGNORECASE)
    for line in lines:
        if chuong_pattern.match(line):
            current_dieu = current_khoan = None
        elif muc_pattern.match(line):
            current_dieu = current_khoan = None
        elif dieu_pattern.match(line):
            current_dieu = dieu_pattern.match(line).group(2)
            current_khoan = None
            leading = len(line) - len(line.lstrip())
            line = line[:leading] + f'<a id="d{current_dieu}"></a>' + line[leading:]
        elif current_dieu and khoan_pattern.match(line):
            m = khoan_pattern.match(line)
            current_khoan = m.group(2)
            line = m.group(1) + f'<a id="d{current_dieu}k{current_khoan}"></a>' + line[len(m.group(1)):]
        elif current_dieu and current_khoan and diem_pattern.match(line):
            m = diem_pattern.match(line)
            diem_char = m.group(2).lower()
            line = m.group(1) + f'<a id="d{current_dieu}k{current_khoan}d{diem_char}"></a>' + line[len(m.group(1)):]
        output_lines.append(line)
    return "\n".join(output_lines)


def inject_warning_block(markdown_content: str, target_anchor: str, amendment_source: str, source_doc_path: str) -> str:
    """Inject a markdown warning block immediately after the line containing target_anchor."""
    lines = markdown_content.splitlines()
    anchor_pattern = f'id="{target_anchor}"'
    target_idx = -1
    for idx, line in enumerate(lines):
        if anchor_pattern in line:
            target_idx = idx
            break
    if target_idx == -1:
        return markdown_content
    doc_title = amendment_source
    match = re.match(r"^(Điều\s+\d+(?:\s+Khoản\s+\d+)?(?:\s+Điểm\s+[a-zA-ZđĐ])?)\s+(.*)$", amendment_source, re.IGNORECASE)
    if match:
        doc_title = match.group(2).strip()
    warning_text = f"> [!WARNING] Khoản này đã bị sửa đổi/bổ sung bởi {amendment_source}. Xem nội dung mới tại [{doc_title}]({source_doc_path})."
    already_exists = False
    for offset in range(1, 4):
        if target_idx + offset < len(lines):
            check_line = lines[target_idx + offset]
            if "[!WARNING]" in check_line and (source_doc_path in check_line or amendment_source in check_line):
                already_exists = True
                break
    if not already_exists:
        lines.insert(target_idx + 1, warning_text)
    return "\n".join(lines)
