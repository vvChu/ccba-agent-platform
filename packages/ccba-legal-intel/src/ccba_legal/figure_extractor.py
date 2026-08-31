# Copyright (c) 2026 CCBA. All rights reserved.
"""Universal Technical Figure Extractor & Spatial Knowledge Cataloger (OKF v2.2 - ADR 0030 / ADR 0031)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

import yaml
from docx import Document

AERODYNAMIC_FIGURES_GEOMETRY: dict[str, dict[str, Any]] = {
    "C.1": {
        "description": "Mặt cao độ công trình quy ước z0 (mốc chuẩn) trên địa hình nghiêng dốc",
        "parameters": ["z0 (mốc chuẩn quy ước)", "i (độ dốc mặt đất)", "z (cao độ tính toán)"],
        "cases": [
            "i <= 0.3: z tính từ mặt đất thực tế",
            "0.3 < i < 2: z tính từ mặt cao độ công trình quy ước z0",
            "i >= 2: z tính từ đáy công trình hoặc vách đứng",
        ],
    },
    "E.1": {
        "description": "Kích thước tương đương cho các mặt bằng phức tạp (chữ L, U, T, chữ thập, thắt eo)",
        "parameters": ["b (chiều rộng tương đương)", "d (chiều sâu tương đương)", "e = min(b, 2h)"],
    },
    "F.1": {
        "description": "Phân vùng khí động trên tường phẳng, hàng rào và kết cấu tương tự",
        "parameters": ["e = min(b, 2h)", "h (chiều cao)", "l (chiều dài)"],
        "zones": ["Vùng A (biên mép đón gió)", "Vùng B (dải tiếp theo)", "Vùng C (phần giữa)", "Vùng D (mặt đón gió)", "Vùng E (mặt hút gió)"],
        "related_tables": ["F.1"],
    },
    "F.2": {
        "description": "Sơ đồ khí động cho bảng quảng cáo trên mặt đất và trên cao",
        "parameters": ["b (chiều rộng)", "h (chiều cao)", "zg (khoảng hở đáy)"],
        "related_tables": ["F.2"],
    },
    "F.3": {
        "description": "Phân vùng khí động mái bằng (góc dốc alpha <= 5 độ)",
        "parameters": ["e = min(b, 2h)", "hp (chiều cao tường chắn mái parapet)"],
        "zones": ["Vùng F (góc mái e/4 x e/10)", "Vùng G (dải mép đón gió e/10)", "Vùng H (dải giữa mái)", "Vùng I (phần diện tích còn lại)"],
        "related_tables": ["F.3a", "F.3b"],
    },
    "F.4": {
        "description": "Phân vùng khí động mái dốc một phía (alpha từ 5 đến 75 độ)",
        "parameters": ["e = min(b, 2h)", "b (cạnh vuông góc hướng gió)", "alpha (góc dốc)"],
        "zones": ["Vùng F (góc đón gió)", "Vùng G (mép đón gió)", "Vùng H (diện tích giữa)", "Vùng I (mép nóc/khuất gió)"],
        "related_tables": ["F.3a", "F.3b"],
    },
    "F.5a": {
        "description": "Phân vùng khí động tường thẳng đứng của nhà có mặt bằng chữ nhật",
        "parameters": ["e = min(b, 2h)", "d (chiều sâu dọc hướng gió)", "b (bề rộng đón gió)"],
        "zones": ["Vùng A (dải mép biên e/5)", "Vùng B (dải giữa 4e/5)", "Vùng C (dải cuối tường)", "Vùng D (toàn bộ tường đón gió)", "Vùng E (toàn bộ tường hút gió)"],
        "related_tables": ["F.4a", "F.4b"],
    },
    "F.5b": {
        "description": "Phân vùng khí động tường nghiêng của nhà có mặt bằng chữ nhật",
        "parameters": ["alpha (góc nghiêng của tường so với phương thẳng đứng)"],
        "related_tables": ["F.4a", "F.4b"],
    },
    "F.6": {
        "description": "Phân vùng khí động mái dốc hai phía của nhà có mặt bằng chữ nhật",
        "parameters": ["e = min(b, 2h)", "alpha (góc dốc mái)", "theta (góc hướng gió 0, 90, 180 độ)"],
        "zones": [
            "Vùng F: Góc mép đón gió (kích thước e/4 x e/10)",
            "Vùng G: Dải mép đón gió giữa hai vùng F (chiều rộng e/10)",
            "Vùng H: Phần diện tích còn lại của nửa mái đón gió",
            "Vùng I: Phần diện tích chính của nửa mái khuất gió",
            "Vùng J: Dải mép nóc nửa mái khuất gió (chiều rộng e/10)",
        ],
        "related_tables": ["F.5a", "F.5b"],
    },
    "F.7": {
        "description": "Phân vùng khí động mái dốc bốn phía (mái hông / hipped roof)",
        "parameters": ["e = min(b, 2h)", "alpha (góc dốc)"],
        "zones": ["Vùng F, G, H trên mái đón gió; Vùng I, J trên mái khuất gió; Vùng M, N trên mái hông"],
        "related_tables": ["F.6a", "F.6b"],
    },
    "F.8": {
        "description": "Phân bố hệ số khí động ce trên bề mặt mái vòm và mái gần giống vòm",
        "parameters": ["f (độ võng vòm)", "d (nhịp vòm)", "h (chiều cao vách đứng)"],
        "zones": ["Vùng A (chân vòm đón gió)", "Vùng B (đỉnh vòm)", "Vùng C (chân vòm khuất gió)"],
        "related_tables": ["F.7a", "F.7b"],
    },
}




def load_bundle_figures_overrides(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    """Load bundle-level figure metadata overrides from `figures_override.yaml` if present."""
    override_file = bundle_dir / "figures_override.yaml"
    if not override_file.exists():
        return {}
    try:
        data = yaml.safe_load(override_file.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def extract_docx_figures(
    docx_path: str | Path,
    output_dir: str | Path,
    standard_name: str | None = None
) -> dict[str, Any]:
    """Extract all technical figures from DOCX and build OKF figures catalog."""
    docx_p = Path(docx_path)
    out_p = Path(output_dir)
    figures_dir = out_p if out_p.name == "figures" else out_p / "figures"
    bundle_dir = figures_dir.parent if figures_dir.parent.exists() else figures_dir
    images_dir = figures_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    fig_overrides = load_bundle_figures_overrides(bundle_dir)
    std_name = standard_name or docx_p.stem.upper().replace("_", " ")

    doc = Document(docx_p)
    rels = doc.part.rels

    # 1. Identify all Figure captions
    fig_items: list[dict[str, Any]] = []
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        m = re.match(r"^(?:Hình|HÌNH)\s+([A-Za-z0-9\.\-]+)\s*[-–—:]\s*(.+)$", text)
        if m:
            fig_tag = m.group(1).strip()
            fig_title = m.group(2).strip()
            fig_items.append({
                "p_idx": idx,
                "tag": fig_tag,
                "title": fig_title,
                "slug": fig_tag.lower().replace(".", "_").replace("-", "_")
            })

    existing_tags = {item["tag"] for item in fig_items}
    for o_tag, o_val in fig_overrides.items():
        str_tag = str(o_tag)
        if str_tag not in existing_tags and isinstance(o_val, dict) and "title" in o_val:
            f_slug = str_tag.lower().replace(".", "_").replace("-", "_")
            fig_items.append({
                "p_idx": o_val.get("p_idx", -1),
                "tag": str_tag,
                "title": o_val["title"],
                "slug": f_slug,
                "media": o_val.get("media"),
                "annex": o_val.get("annex", "MAIN"),
            })

    def _fig_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        t = item["tag"]
        if t.isdigit():
            return (0, int(t), "")
        m_num = re.match(r"^([A-Za-z]+)\.?([0-9]+)?", t)
        if m_num:
            prefix = m_num.group(1)
            num = int(m_num.group(2)) if m_num.group(2) else 0
            return (1, num, prefix)
        return (2, 0, t)

    fig_items.sort(key=_fig_sort_key)

    # 2. Extract media images from docx zip
    catalog_entries: list[dict[str, Any]] = []
    cards_dir = figures_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_p) as z:
        media_list = sorted([f for f in z.namelist() if f.startswith("word/media/")])

        # Unconditionally extract all media files so any inline diagram image is present
        for media_path in media_list:
            fname = Path(media_path).name
            target_file = images_dir / fname
            if not target_file.exists():
                target_file.write_bytes(z.read(media_path))

        if fig_items:
            for i, item in enumerate(fig_items):
                f_idx = item["p_idx"]
                f_tag = item["tag"]
                f_title = item["title"]
                f_slug = item["slug"]
                out_filename = f"hinh_{f_slug}.png"
                out_img_path = images_dir / out_filename

                if item.get("media"):
                    media_path = item["media"]
                    if not media_path.startswith("word/"):
                        media_path = f"word/{media_path}"
                    if media_path in z.namelist():
                        data = z.read(media_path)
                        out_img_path.write_bytes(data)
                elif f_idx >= 0:
                    prev_idx = fig_items[i - 1]["p_idx"] if i > 0 and fig_items[i - 1]["p_idx"] >= 0 else max(0, f_idx - 15)
                    search_start = max(prev_idx + 1, f_idx - 6)

                    # Search bounded range before f_idx
                    found_media: list[str] = []
                    sub_items: list[tuple[Any, str]] = []
                    for k in range(search_start, f_idx):
                        pk = doc.paragraphs[k]
                        m_rids = re.findall(r'r:(?:id|embed)="([^"]+)"', pk._element.xml)
                        for rid in m_rids:
                            if rid in rels:
                                target = rels[rid].target_ref
                                if target.startswith("media/image") and target not in found_media:
                                    found_media.append(target)
                                    full_m_p = f"word/{target}"
                                    if full_m_p in z.namelist() and not target.endswith(".wmf"):
                                        sub_cap = ""
                                        for next_k in range(k + 1, min(k + 3, f_idx)):
                                            nxt_txt = doc.paragraphs[next_k].text.strip()
                                            if re.match(r"^[a-z]\)\s*", nxt_txt):
                                                sub_cap = nxt_txt
                                                break
                                        import io

                                        from PIL import Image, ImageDraw, ImageFont
                                        sub_img = Image.open(io.BytesIO(z.read(full_m_p)))
                                        if sub_img.width >= 120 and sub_img.height >= 60:
                                            sub_items.append((sub_img, sub_cap))

                    if len(sub_items) > 1:
                        try:
                            font_bold = ImageFont.truetype("arialbd.ttf", 13)
                        except Exception:
                            font_bold = ImageFont.load_default()

                        dummy_img = Image.new("RGB", (1, 1))
                        dummy_draw = ImageDraw.Draw(dummy_img)
                        text_widths = [dummy_draw.textbbox((0, 0), cap, font=font_bold)[2] - dummy_draw.textbbox((0, 0), cap, font=font_bold)[0] for _, cap in sub_items if cap]
                        max_img_w = max(img.width for img, _ in sub_items)
                        max_txt_w = max(text_widths) if text_widths else 0
                        canvas_w = max(max_img_w, max_txt_w) + 60

                        total_h = 15
                        for img, cap in sub_items:
                            total_h += img.height + (35 if cap else 15)

                        comp = Image.new("RGB", (canvas_w, total_h), color=(255, 255, 255))
                        draw = ImageDraw.Draw(comp)
                        curr_y = 15
                        for img, cap in sub_items:
                            offset_x = (canvas_w - img.width) // 2
                            comp.paste(img, (offset_x, curr_y))
                            curr_y += img.height + 6
                            if cap:
                                bbox = draw.textbbox((0, 0), cap, font=font_bold)
                                cap_w = bbox[2] - bbox[0]
                                tx = max(10, (canvas_w - cap_w) // 2)
                                draw.text((tx, curr_y), cap, fill=(0, 0, 0), font=font_bold)
                                curr_y += 28
                        comp.save(out_img_path, "PNG")
                    elif found_media:
                        media_path = f"word/{found_media[-1]}"
                        if media_path in z.namelist():
                            data = z.read(media_path)
                            out_img_path.write_bytes(data)
                    elif i < len(media_list):
                        data = z.read(media_list[i])
                        out_img_path.write_bytes(data)



                # Build metadata
                annex = item.get("annex") or (f_tag[0] if f_tag[0].isalpha() else "MAIN")
                geom = fig_overrides.get(f_tag, {})
                if isinstance(geom, dict) and "geometry_rules" in geom:
                    geom = geom["geometry_rules"]

                entry: dict[str, Any] = {
                    "figure_id": f"FIG_{f_slug.upper()}",
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
                card_content = render_markdown_figure_card(entry)
                (cards_dir / f"hinh_{f_slug}.md").write_text(card_content, encoding="utf-8")
        else:
            for idx, media_path in enumerate(media_list, 1):
                ext = Path(media_path).suffix or ".png"
                out_filename = f"hinh_{idx}{ext}"
                out_img_path = images_dir / out_filename
                data = z.read(media_path)
                out_img_path.write_bytes(data)
                entry = {
                    "figure_id": f"FIG_{idx}",
                    "tag": str(idx),
                    "title": f"Hình {idx}",
                    "annex": "MAIN",
                    "anchor": f"hinh-{idx}",
                    "image_relpath": f"figures/images/{out_filename}",
                    "has_image": True
                }
                catalog_entries.append(entry)
                card_content = render_markdown_figure_card(entry)
                (cards_dir / f"hinh_{idx}.md").write_text(card_content, encoding="utf-8")

    # 3. Write figures_catalog.yaml
    manifest = {
        "standard": std_name,
        "total_figures": len(catalog_entries),
        "figures": catalog_entries
    }
    catalog_path = figures_dir / "figures_catalog.yaml"
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
        f'<p align="center">\n\n![Hình {tag}]({img_path})\n\n</p>\n',
        f'<p align="center"><strong>Hình {tag} — {title}</strong></p>\n'
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


# Public Alias
extract_technical_figures = extract_docx_figures

