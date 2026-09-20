"""Markdown Architecture Specification Matrix generator adhering to Visual Ergonomics Standard v8.15.10."""

from __future__ import annotations

import re
from typing import Any


def _clean_markdown_text(text: str) -> str:
    """Clean and sanitize text for Markdown table cell rendering."""
    # Strip leaked HTML entity brackets in prose
    text = text.replace("#40;", "(").replace("#41;", ")")
    # Replace newlines with space
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    # Escape unescaped pipes in wikilinks: [[slug|alias]] -> [[slug\|alias]]
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"[[\1\|\2]]", text)
    # Escape standalone pipes
    # (avoid re-escaping \|)
    parts = re.split(r"(\[\[.*?\]\])", text)
    for i, p in enumerate(parts):
        if not p.startswith("[["):
            parts[i] = p.replace("|", "/")
    return "".join(parts)


def generate_markdown_spec_table(
    elements: list[dict[str, Any]],
    table_title: str = "Bảng Đặc Tả Ma Trận Kiến Trúc",
) -> str:
    """Generate Markdown Architectural Specification Table from Excalidraw elements.

    Adheres strictly to CCBA Ergonomics Standards (escape pipe wikilinks, non-breaking arrow,
    baseline subtitle stabilization, zero code-pill links, isolated parentheses).

    Args:
        elements: List of Excalidraw element dicts.
        table_title: Title header for the specification table.

    Returns:
        Formatted Markdown table string.
    """
    shapes: dict[str, dict[str, Any]] = {}
    arrows: list[dict[str, Any]] = []
    text_nodes: dict[str, str] = {}

    for el in elements:
        t = el.get("type")
        eid = el.get("id", "")
        if t in ("rectangle", "ellipse", "diamond"):
            shapes[eid] = el
        elif t == "arrow":
            arrows.append(el)
        elif t == "text":
            text_nodes[eid] = str(el.get("text", "")).strip()

    if not shapes:
        return "*(Không có nút hình học để tạo bảng đặc tả ma trận)*"

    # Map bound texts to shapes
    shape_labels: dict[str, str] = {}
    for sid, s in shapes.items():
        labels = []
        if s.get("text"):
            labels.append(str(s["text"]).strip())
        for b in s.get("boundElements", []):
            if isinstance(b, dict) and b.get("id") in text_nodes:
                labels.append(text_nodes[b["id"]])
        for el in elements:
            if el.get("type") == "text" and el.get("containerId") == sid:
                labels.append(str(el.get("text", "")).strip())

        full_label = " - ".join(dict.fromkeys(labels)) if labels else f"Node `{sid}`"
        shape_labels[sid] = _clean_markdown_text(full_label)

    # Map incoming and outgoing connections
    connections: dict[str, list[str]] = {sid: [] for sid in shapes}
    for arr in arrows:
        sb = arr.get("startBinding", {})
        eb = arr.get("endBinding", {})
        sid = sb.get("elementId") if isinstance(sb, dict) else (sb if isinstance(sb, str) else None)
        eid = eb.get("elementId") if isinstance(eb, dict) else (eb if isinstance(eb, str) else None)

        if sid in shapes and eid in shapes:
            target_label = shape_labels[eid]
            # Truncate target label if too long
            if len(target_label) > 35:
                target_label = target_label[:32] + "..."
            arrow_label = ""
            for b in arr.get("boundElements", []):
                if isinstance(b, dict) and b.get("id") in text_nodes:
                    arrow_label = f" *({text_nodes[b['id']]})*"
                    break
            connections[sid].append(f"↳&nbsp;{target_label}{arrow_label}")

    lines = [
        f"### 📋 {table_title}",
        "",
        "| STT | Thành Phần / Nút Kiến Trúc | Phân Loại & Hình Khối | Kết Nối Đến / Luồng Dữ Liệu |",
        "| :---: | :--- | :--- | :--- |",
    ]

    for idx, (sid, shape) in enumerate(shapes.items(), 1):
        label = shape_labels[sid]
        stype = shape.get("type", "rectangle").capitalize()
        # Add visual subtitle anchor if applicable
        bg = shape.get("backgroundColor", "")
        role = "Thành phần tiêu chuẩn"
        if bg in ("#e3f2fd", "#0d47a1") or shape.get("strokeWidth", 1) >= 3:
            role = "**Lõi Điều Phối (Hub/Core)**"
        elif shape.get("strokeStyle") == "dashed":
            role = "*Hỗ trợ / Tham chiếu*"
        elif stype == "Diamond":
            role = "**Điểm Quyết Định / Biên**"

        type_cell = f"{role} *(Hình {stype})*"
        conn_cell = (
            "<br>".join(connections[sid]) if connections[sid] else "*(Điểm đích / Không có)*"
        )

        lines.append(f"| {idx} | {label} | {type_cell} | {conn_cell} |")

    lines.append("")
    return "\n".join(lines)
