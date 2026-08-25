# Copyright (c) 2026 CCBA. All rights reserved.
"""Universal Technical Figure Extractor & Spatial Knowledge Cataloger (OKF v2.2 - ADR 0030 / ADR 0031)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
import yaml


# Standard Geometric Rules & Table Mappings for Wind Load Engineering Figures (Phụ lục F)
AERODYNAMIC_FIGURES_GEOMETRY: dict[str, dict[str, Any]] = {
    "C.1": {
        "description": "Mặt cao độ công trình quy ước z0 (mốc chuẩn) trên địa hình nghiêng dốc",
        "parameters": ["z0 (mốc chuẩn quy ước)", "i (độ dốc mặt đất)", "z (cao độ tính toán)"],
        "cases": [
            "i <= 0.3: z tính từ mặt đất thực tế",
            "0.3 < i < 2: z tính từ mặt cao độ công trình quy ước z0",
            "i >= 2: z tính từ đáy công trình hoặc vách đứng"
        ]
    },
    "E.1": {
        "description": "Kích thước tương đương cho các mặt bằng phức tạp (chữ L, U, T, chữ thập, thắt eo)",
        "parameters": ["b (chiều rộng tương đương)", "d (chiều sâu tương đương)", "e = min(b, 2h)"]
    },
    "F.1": {
        "description": "Phân vùng khí động trên tường phẳng, hàng rào và kết cấu tương tự",
        "parameters": ["e = min(b, 2h)", "h (chiều cao)", "l (chiều dài)"],
        "zones": ["Vùng A (biên mép đón gió)", "Vùng B (dải tiếp theo)", "Vùng C (phần giữa)", "Vùng D (mặt đón gió)", "Vùng E (mặt hút gió)"],
        "related_tables": ["F.1"]
    },
    "F.2": {
        "description": "Sơ đồ khí động cho bảng quảng cáo trên mặt đất và trên cao",
        "parameters": ["b (chiều rộng)", "h (chiều cao)", "zg (khoảng hở đáy)"],
        "related_tables": ["F.2"]
    },
    "F.3": {
        "description": "Phân vùng khí động mái bằng (góc dốc alpha <= 5 độ)",
        "parameters": ["e = min(b, 2h)", "hp (chiều cao tường chắn mái parapet)"],
        "zones": ["Vùng F (góc mái e/4 x e/10)", "Vùng G (dải mép đón gió e/10)", "Vùng H (dải giữa mái)", "Vùng I (phần diện tích còn lại)"],
        "related_tables": ["F.3a", "F.3b"]
    },
    "F.4": {
        "description": "Phân vùng khí động mái dốc một phía (alpha từ 5 đến 75 độ)",
        "parameters": ["e = min(b, 2h)", "b (cạnh vuông góc hướng gió)", "alpha (góc dốc)"],
        "zones": ["Vùng F (góc đón gió)", "Vùng G (mép đón gió)", "Vùng H (diện tích giữa)", "Vùng I (mép nóc/khuất gió)"],
        "related_tables": ["F.3a", "F.3b"]
    },
    "F.5a": {
        "description": "Phân vùng khí động tường thẳng đứng của nhà có mặt bằng chữ nhật",
        "parameters": ["e = min(b, 2h)", "d (chiều sâu dọc hướng gió)", "b (bề rộng đón gió)"],
        "zones": ["Vùng A (dải mép biên e/5)", "Vùng B (dải giữa 4e/5)", "Vùng C (dải cuối tường)", "Vùng D (toàn bộ tường đón gió)", "Vùng E (toàn bộ tường hút gió)"],
        "related_tables": ["F.4a", "F.4b"]
    },
    "F.5b": {
        "description": "Phân vùng khí động tường nghiêng của nhà có mặt bằng chữ nhật",
        "parameters": ["alpha (góc nghiêng của tường so với phương thẳng đứng)"],
        "related_tables": ["F.4a", "F.4b"]
    },
    "F.6": {
        "description": "Phân vùng khí động mái dốc hai phía của nhà có mặt bằng chữ nhật",
        "parameters": ["e = min(b, 2h)", "alpha (góc dốc mái)", "theta (góc hướng gió 0, 90, 180 độ)"],
        "zones": [
            "Vùng F: Góc mép đón gió (kích thước e/4 x e/10)",
            "Vùng G: Dải mép đón gió giữa hai vùng F (chiều rộng e/10)",
            "Vùng H: Phần diện tích còn lại của nửa mái đón gió",
            "Vùng I: Phần diện tích chính của nửa mái khuất gió",
            "Vùng J: Dải mép nóc nửa mái khuất gió (chiều rộng e/10)"
        ],
        "related_tables": ["F.5a", "F.5b"]
    },
    "F.7": {
        "description": "Phân vùng khí động mái dốc bốn phía (mái hông / hipped roof)",
        "parameters": ["e = min(b, 2h)", "alpha (góc dốc)"],
        "zones": ["Vùng F, G, H trên mái đón gió; Vùng I, J trên mái khuất gió; Vùng M, N trên mái hông"],
        "related_tables": ["F.6a", "F.6b"]
    },
    "F.8": {
        "description": "Phân bố hệ số khí động ce trên bề mặt mái vòm và mái gần giống vòm",
        "parameters": ["f (độ võng vòm)", "d (nhịp vòm)", "h (chiều cao vách đứng)"],
        "zones": ["Vùng A (chân vòm đón gió)", "Vùng B (đỉnh vòm)", "Vùng C (chân vòm khuất gió)"],
        "related_tables": ["F.7a", "F.7b"]
    }
}


def extract_docx_figures(
    docx_path: str | Path,
    output_dir: str | Path
) -> dict[str, Any]:
    """Extract all technical figures from DOCX and build OKF figures catalog."""
    docx_p = Path(docx_path)
    out_p = Path(output_dir)
    figures_dir = out_p if out_p.name == "figures" else out_p / "figures"
    images_dir = figures_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    doc = Document(docx_p)
    rels = doc.part.rels

    # 1. Identify all Figure captions
    fig_items: list[dict[str, Any]] = []
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        m = re.match(r"^Hình\s+([A-H]\.[0-9]+[a-z]?|[0-9]+)\s*[-–—]\s*(.+)$", text)
        if m:
            fig_tag = m.group(1).strip()
            fig_title = m.group(2).strip()
            fig_items.append({
                "p_idx": idx,
                "tag": fig_tag,
                "title": fig_title,
                "slug": fig_tag.lower().replace(".", "_")
            })

    # 2. Extract media images from docx zip
    catalog_entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(docx_p) as z:
        for i, item in enumerate(fig_items):
            f_idx = item["p_idx"]
            f_tag = item["tag"]
            f_title = item["title"]
            f_slug = item["slug"]
            prev_idx = fig_items[i - 1]["p_idx"] if i > 0 else max(0, f_idx - 15)

            # Search backwards from f_idx
            found_media: list[str] = []
            for k in range(prev_idx + 1, f_idx + 2):
                if k >= len(doc.paragraphs):
                    break
                pk = doc.paragraphs[k]
                m_rids = re.findall(r'r:(?:id|embed)="([^"]+)"', pk._element.xml)
                for rid in m_rids:
                    if rid in rels:
                        target = rels[rid].target_ref
                        if target.startswith("media/image") and target not in found_media:
                            found_media.append(target)

            out_filename = f"hinh_{f_slug}.png"
            out_img_path = images_dir / out_filename
            
            if found_media:
                media_path = f"word/{found_media[-1]}"
                if media_path in z.namelist():
                    data = z.read(media_path)
                    out_img_path.write_bytes(data)

            # Build metadata
            annex = f_tag[0] if f_tag[0].isalpha() else "MAIN"
            geom = AERODYNAMIC_FIGURES_GEOMETRY.get(f_tag, {})

            entry: dict[str, Any] = {
                "figure_id": f"FIG_TCVN2737_{f_slug.upper()}",
                "tag": f_tag,
                "title": f_title,
                "annex": annex,
                "anchor": f"hinh-{f_slug}",
                "image_relpath": f"figures/images/{out_filename}",
                "has_image": out_img_path.exists()
            }
            if geom:
                entry["geometry_rules"] = geom

            catalog_entries.append(entry)

    # 3. Write figures_catalog.yaml
    manifest = {
        "standard": "TCVN 2737:2023",
        "total_figures": len(catalog_entries),
        "figures": catalog_entries
    }
    catalog_path = out_p / "figures_catalog.yaml"
    with open(catalog_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, allow_unicode=True, sort_keys=False, indent=2)

    return manifest


def render_markdown_figure_card(fig_entry: dict[str, Any]) -> str:
    """Render standardized Markdown Figure Card with anchor and geometric callouts."""
    tag = fig_entry["tag"]
    title = fig_entry["title"]
    anchor = fig_entry["anchor"]
    img_path = fig_entry["image_relpath"]
    geom = fig_entry.get("geometry_rules", {})

    lines: list[str] = [
        f'\n<a id="{anchor}"></a>\n',
        f'![Hình {tag}]({img_path})\n',
        f'**Hình {tag} — {title}**\n'
    ]

    if geom:
        callout_lines = ["> [!NOTE]", "> **Đặc tả Hình học & Tham chiếu Khí động:**"]
        if "description" in geom:
            callout_lines.append(f'> \\- **Phạm vi:** {geom["description"]}')
        if "parameters" in geom:
            callout_lines.append(f'> \\- **Thông số cơ sở:** {", ".join(geom["parameters"])}')
        if "zones" in geom:
            callout_lines.append("> \\- **Phân vùng khí động:**")
            for z in geom["zones"]:
                callout_lines.append(f'> &nbsp;&nbsp;+ {z}')
        if "related_tables" in geom:
            table_links = [f'[{t}](#bang-bang-{t.lower().replace(".", "-")})' for t in geom["related_tables"]]
            callout_lines.append(f'> \\- **Bảng tra liên kết:** {", ".join(table_links)}')
        
        lines.append("\n".join(callout_lines) + "\n")

    return "\n".join(lines) + "\n"
