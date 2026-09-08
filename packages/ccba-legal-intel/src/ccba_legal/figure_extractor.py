# Copyright (c) 2026 CCBA. All rights reserved.
"""Universal Technical Figure Extractor & Spatial Knowledge Cataloger (OKF v2.2 - ADR 0030 / ADR 0031)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

import yaml
from docx import Document

from ccba_legal.constants import (
    CURRENT_OKF_SPEC,
    FIGURES_CATALOG_SCHEMA_VERSION,
)


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


def parse_table_figures(tbl_el: Any) -> list[tuple[str, str]]:
    """Extract (rId, sub_caption) pairs from a table layout element."""
    rows = tbl_el.xpath(".//w:tr")
    grid_cells: list[list[dict[str, Any]]] = []
    for r in rows:
        row_cells = []
        for c in r.xpath(".//w:tc"):
            rids = c.xpath(".//@r:embed | .//@r:id")
            txt = " ".join("".join(c.itertext()).split())
            row_cells.append({"rids": rids, "txt": txt})
        grid_cells.append(row_cells)

    extracted: list[tuple[str, str]] = []
    num_rows = len(grid_cells)
    for r_idx, row in enumerate(grid_cells):
        for c_idx, cell in enumerate(row):
            for rid in cell["rids"]:
                cap = ""
                m_cap = re.search(r"([a-z0-9đĐ]\s*[-–—\)]\s*[^;\n\r]+)", cell["txt"], re.IGNORECASE)
                if m_cap:
                    cap = m_cap.group(1).strip()
                elif r_idx + 1 < num_rows and c_idx < len(grid_cells[r_idx + 1]):
                    next_txt = grid_cells[r_idx + 1][c_idx]["txt"]
                    m_next = re.search(
                        r"([a-z0-9đĐ]\s*[-–—\)]\s*[^;\n\r]+)", next_txt, re.IGNORECASE
                    )
                    if m_next:
                        cap = m_next.group(1).strip()
                if cap:
                    for k in (4, 3, 2):
                        if len(cap) % k == 0:
                            chunk = cap[: len(cap) // k]
                            if chunk * k == cap:
                                cap = chunk
                                break
                extracted.append((rid, cap))
    return extracted


def extract_docx_figures(
    docx_path: str | Path, output_dir: str | Path, standard_name: str | None = None
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

    doc = Document(str(docx_p))
    rels = doc.part.rels
    body_elems = doc.element.body[:]

    p_to_b: dict[int, int] = {}
    p_counter = 0
    for b_idx, el in enumerate(body_elems):
        if el.tag.endswith("p"):
            p_to_b[p_counter] = b_idx
            p_counter += 1

    # 1. Identify all Figure captions
    current_annex = "MAIN"
    fig_items: list[dict[str, Any]] = []
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        m_annex = re.search(r"PHỤ\s+LỤC\s+([A-Za-z0-9Đđ]+)", text, re.IGNORECASE)
        if m_annex:
            current_annex = m_annex.group(1).upper()
        m = re.match(
            r"^(?:Hình|HÌNH)\s+([0-9A-Za-zĐđ]+(?:\.[0-9A-Za-zĐđ]+)*)\s*[\.\-–—:]\s*(.+)$", text
        )
        if m:
            fig_tag = m.group(1).strip()
            fig_title = m.group(2).strip()
            fig_items.append(
                {
                    "p_idx": idx,
                    "tag": fig_tag,
                    "title": fig_title,
                    "slug": fig_tag.lower().replace("đ", "dd").replace(".", "_").replace("-", "_"),
                    "annex": current_annex,
                }
            )

    existing_tags = {item["tag"] for item in fig_items}
    for o_tag, o_val in fig_overrides.items():
        str_tag = str(o_tag)
        if str_tag not in existing_tags and isinstance(o_val, dict) and "title" in o_val:
            f_slug = str_tag.lower().replace("đ", "dd").replace(".", "_").replace("-", "_")
            fig_items.append(
                {
                    "p_idx": o_val.get("p_idx", -1),
                    "tag": str_tag,
                    "title": o_val["title"],
                    "slug": f_slug,
                    "media": o_val.get("media"),
                    "annex": o_val.get("annex", "MAIN"),
                }
            )

    fig_items.sort(key=lambda x: (0 if x["p_idx"] >= 0 else 1, x["p_idx"], x["tag"]))

    # 2. Extract media images from docx zip
    catalog_entries: list[dict[str, Any]] = []
    cards_dir = figures_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    images_dir = figures_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_p) as z:
        media_list = sorted([f for f in z.namelist() if f.startswith("word/media/")])

        # Extract raster media files only (protecting against stray .wmf/.emf binaries)
        allowed_raster_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
        for media_path in media_list:
            fname = Path(media_path).name
            if Path(fname).suffix.lower() in allowed_raster_exts:
                target_file = images_dir / fname
                if not target_file.exists():
                    target_file.write_bytes(z.read(media_path))

        if fig_items:
            consumed_media: set[str] = set()
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
                        consumed_media.add(media_path.replace("word/", ""))
                elif f_idx >= 0:
                    b_f_idx = p_to_b.get(f_idx, f_idx)
                    prev_b_idx = (
                        fig_items[i - 1].get(
                            "search_end_b", p_to_b.get(fig_items[i - 1]["p_idx"], -1)
                        )
                        if i > 0 and fig_items[i - 1]["p_idx"] >= 0
                        else max(0, b_f_idx - 35)
                    )
                    search_start_b = max(prev_b_idx + 1, b_f_idx - 30)

                    # Check if there is a (kết thúc) continuation paragraph after f_idx
                    search_end_b = b_f_idx
                    for next_idx in range(f_idx + 1, min(f_idx + 6, len(doc.paragraphs))):
                        nxt_p = doc.paragraphs[next_idx].text.strip()
                        if re.match(
                            rf"^(?:Hình|HÌNH)\s+{re.escape(f_tag)}\s*\((?:kết\s+thúc|tiếp\s+theo)\)",
                            nxt_p,
                            re.IGNORECASE,
                        ):
                            search_end_b = p_to_b.get(next_idx, b_f_idx) + 1
                            break

                    item["search_end_b"] = search_end_b

                    # Search bounded range for figure diagrams (both paragraphs and layout tables)
                    found_media: list[str] = []
                    sub_items: list[tuple[Any, str, str]] = []
                    import io

                    from PIL import Image, ImageDraw, ImageFont

                    for b_k in range(search_start_b, search_end_b):
                        el = body_elems[b_k]
                        if el.tag.endswith("tbl"):
                            tbl_figs = parse_table_figures(el)
                            for rid, sub_cap in tbl_figs:
                                if rid in rels:
                                    target = rels[rid].target_ref
                                    if (
                                        target.startswith("media/image")
                                        and target not in consumed_media
                                        and Path(target).suffix.lower() in allowed_raster_exts
                                    ):
                                        full_m_p = f"word/{target}"
                                        if full_m_p in z.namelist():
                                            try:
                                                sub_img = Image.open(io.BytesIO(z.read(full_m_p)))
                                                if sub_img.width >= 100 and sub_img.height >= 50:
                                                    sub_items.append((sub_img, sub_cap, target))
                                                    found_media.append(target)
                                            except Exception:
                                                pass
                        elif el.tag.endswith("p"):
                            m_rids = re.findall(r'r:(?:id|embed)="([^"]+)"', el.xml)
                            for rid in m_rids:
                                if rid in rels:
                                    target = rels[rid].target_ref
                                    if (
                                        target.startswith("media/image")
                                        and target not in consumed_media
                                        and Path(target).suffix.lower() in allowed_raster_exts
                                    ):
                                        full_m_p = f"word/{target}"
                                        if full_m_p in z.namelist():
                                            try:
                                                sub_img = Image.open(io.BytesIO(z.read(full_m_p)))
                                                if sub_img.width >= 100 and sub_img.height >= 50:
                                                    sub_cap = ""
                                                    for next_b in range(
                                                        b_k + 1, min(b_k + 3, search_end_b)
                                                    ):
                                                        nxt_el = body_elems[next_b]
                                                        if nxt_el.tag.endswith("p"):
                                                            nxt_txt = "".join(
                                                                nxt_el.itertext()
                                                            ).strip()
                                                            if (
                                                                re.match(
                                                                    r"^(?:[a-zđĐ]\s*[\)\.\-–—]|[0-9]+\))\s*",
                                                                    nxt_txt,
                                                                    re.IGNORECASE,
                                                                )
                                                                and len(nxt_txt) < 200
                                                                and not re.match(
                                                                    r"^[0-9]+\.", nxt_txt
                                                                )
                                                            ):
                                                                sub_cap = nxt_txt
                                                                break
                                                    sub_items.append((sub_img, sub_cap, target))
                                                    found_media.append(target)
                                            except Exception:
                                                pass

                    # Only stitch sub_items if they are true sub-figures (have a/b sub-captions)
                    # or if this is a multi-part figure with (kết thúc) where all images are large diagrams
                    should_stitch = False
                    if len(sub_items) > 1:
                        has_sub_caps = any(cap for _, cap, _ in sub_items if cap)
                        is_multi_page = (search_end_b > b_f_idx) and all(
                            img.height >= 120 for img, _, _ in sub_items
                        )
                        if has_sub_caps or is_multi_page:
                            should_stitch = True

                    if should_stitch:
                        for _, _, m_t in sub_items:
                            consumed_media.add(m_t)
                        font_bold: Any = None
                        for font_candidate in (
                            "arialbd.ttf",
                            "DejaVuSans-Bold.ttf",
                            "LiberationSans-Bold.ttf",
                            "FreeSansBold.ttf",
                            "arial.ttf",
                        ):
                            try:
                                font_bold = ImageFont.truetype(font_candidate, 13)
                                break
                            except Exception:
                                continue
                        if font_bold is None:
                            font_bold = ImageFont.load_default()

                        dummy_img = Image.new("RGB", (1, 1))
                        dummy_draw = ImageDraw.Draw(dummy_img)
                        text_widths = [
                            dummy_draw.textbbox((0, 0), cap, font=font_bold)[2]
                            - dummy_draw.textbbox((0, 0), cap, font=font_bold)[0]
                            for _, cap, _ in sub_items
                            if cap
                        ]
                        max_img_w = max(img.width for img, _, _ in sub_items)
                        max_txt_w = max(text_widths) if text_widths else 0
                        canvas_w = max(max_img_w, max_txt_w, 660) + 80

                        total_h = 20
                        for img, cap, _ in sub_items:
                            total_h += img.height + (40 if cap else 20)

                        comp = Image.new("RGB", (canvas_w, total_h), color=(255, 255, 255))
                        draw = ImageDraw.Draw(comp)
                        curr_y = 20
                        for img, cap, _ in sub_items:
                            offset_x = (canvas_w - img.width) // 2
                            comp.paste(img, (offset_x, curr_y))
                            curr_y += img.height + 8
                            if cap:
                                bbox = draw.textbbox((0, 0), cap, font=font_bold)
                                cap_w = bbox[2] - bbox[0]
                                tx = max(15, (canvas_w - cap_w) // 2)
                                draw.text((tx, curr_y), cap, fill=(0, 0, 0), font=font_bold)
                                curr_y += 32
                        comp.save(out_img_path, "PNG")
                    elif sub_items:
                        # Pick the diagram image (highest area)
                        best_tgt = sub_items[-1][2]
                        best_area = 0
                        best_img = sub_items[-1][0]
                        for img, _, tgt in sub_items:
                            area = img.width * img.height
                            if area > best_area:
                                best_area = area
                                best_tgt = tgt
                                best_img = img
                        if best_img.mode not in ("RGB", "RGBA"):
                            best_img = best_img.convert("RGB")
                        best_img.save(out_img_path, "PNG")
                        consumed_media.add(best_tgt)

                # Build metadata
                annex = (
                    item.get("annex")
                    if item.get("annex") != "MAIN"
                    else (f_tag[0] if f_tag[0].isalpha() else "MAIN")
                )
                geom = fig_overrides.get(f_tag, {})
                if isinstance(geom, dict) and "geometry_rules" in geom:
                    geom = geom["geometry_rules"]

                entry: dict[str, Any] = {
                    "figure_id": f"FIG_{f_slug.upper()}",
                    "slug": f_slug,
                    "tag": f_tag,
                    "title": f_title,
                    "annex": annex,
                    "anchor": f"hinh-{f_slug}",
                    "image_relpath": f"figures/images/{out_filename}",
                    "has_image": out_img_path.exists(),
                }
                if geom:
                    entry["geometry_rules"] = geom

                catalog_entries.append(entry)
                card_content = render_markdown_figure_card(entry)
                (cards_dir / f"hinh_{f_slug}.md").write_text(card_content, encoding="utf-8")
        else:
            # Document has no captioned figures. Do not fabricate uncaptioned media as numbered figure cards.
            pass

    # 3. Write figures_catalog.yaml
    manifest = {
        "schema_version": FIGURES_CATALOG_SCHEMA_VERSION,
        "okf_spec": CURRENT_OKF_SPEC,
        "standard": std_name,
        "total_figures": len(catalog_entries),
        "figures": catalog_entries,
    }
    catalog_path = figures_dir / "figures_catalog.yaml"
    with open(catalog_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, allow_unicode=True, sort_keys=False, indent=2)

    # 4. Auto-prune orphaned extraction artifacts (Zero-Orphan Policy - ADR 0036)
    scan_and_prune_orphan_figures(bundle_dir, prune=True)

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
        f'<p align="center"><strong>Hình {tag} — {title}</strong></p>\n',
    ]

    if geom:
        callout_lines = ["> [!NOTE]", "> **Đặc tả Hình học & Tham chiếu Khí động:**"]
        if "description" in geom:
            callout_lines.append(f"> \\- **Phạm vi:** {geom['description']}")
        if "parameters" in geom:
            callout_lines.append(f"> \\- **Thông số cơ sở:** {', '.join(geom['parameters'])}")
        if "zones" in geom:
            callout_lines.append("> \\- **Phân vùng khí động:**")
            for z in geom["zones"]:
                callout_lines.append(f"> &nbsp;&nbsp;+ {z}")
        if "related_tables" in geom:
            table_links = [
                f"[{t}](#bang-bang-{t.lower().replace('.', '-')})" for t in geom["related_tables"]
            ]
            callout_lines.append(f"> \\- **Bảng tra liên kết:** {', '.join(table_links)}")

        lines.append("\n".join(callout_lines) + "\n")

    return "\n".join(lines) + "\n"


def scan_and_prune_orphan_figures(bundle_dir: Path, prune: bool = False) -> dict[str, Any]:
    """Scan figures/images in bundle and identify/prune unreferenced orphan images (ADR 0036)."""
    figures_dir = bundle_dir / "figures"
    images_dir = figures_dir / "images"
    if not images_dir.exists():
        return {
            "active": [],
            "orphaned": [],
            "pruned_count": 0,
            "pruned_bytes": 0,
            "total_files": 0,
        }

    all_images = sorted(images_dir.glob("*.*"))
    disk_names = {img.name: img for img in all_images}

    referenced: set[str] = set()

    # 1. In Markdown files
    for md_f in list(bundle_dir.rglob("*.md")):
        if "sources" not in md_f.parts:
            try:
                txt = md_f.read_text(encoding="utf-8")
                for m in re.findall(r"!\[[^\]]*\]\([^)]*images/([^)\s]+)\)", txt):
                    referenced.add(Path(m).name)
                for m in re.findall(
                    r"<img\b[^>]*src=[\"'][^\"']*images/([^\"'\s>]+)[\"']", txt, re.IGNORECASE
                ):
                    referenced.add(Path(m).name)
            except Exception:
                pass

    # 2. In cards/*.json and cards/*.md
    cards_dir = figures_dir / "cards"
    if cards_dir.exists():
        for card_f in list(cards_dir.glob("*.json")) + list(cards_dir.glob("*.md")):
            try:
                txt = card_f.read_text(encoding="utf-8")
                for m in re.findall(r'"image":\s*"([^"]+)"', txt):
                    referenced.add(Path(m).name)
                for m in re.findall(r"!\[[^\]]*\]\([^)]*images/([^)\s]+)\)", txt):
                    referenced.add(Path(m).name)
            except Exception:
                pass

    # 3. In catalogs
    for cat_f in [bundle_dir / "figures_override.yaml", figures_dir / "figures_catalog.yaml"]:
        if cat_f.exists():
            try:
                txt = cat_f.read_text(encoding="utf-8")
                for m in re.findall(r"image_path:\s*\"?([^\s\"]+)\"?", txt):
                    referenced.add(Path(m).name)
                for m in re.findall(r"image_relpath:\s*\"?([^\s\"]+)\"?", txt):
                    referenced.add(Path(m).name)
            except Exception:
                pass

    active = sorted(referenced.intersection(disk_names.keys()))
    orphaned = sorted(disk_names.keys() - referenced)
    pruned_count = 0
    pruned_bytes = 0

    if prune and orphaned:
        for name in orphaned:
            p = disk_names[name]
            pruned_bytes += p.stat().st_size
            try:
                p.unlink()
                pruned_count += 1
            except Exception:
                pass

    return {
        "active": active,
        "orphaned": orphaned,
        "pruned_count": pruned_count,
        "pruned_bytes": pruned_bytes,
        "total_files": len(all_images),
    }


# Public Alias
extract_technical_figures = extract_docx_figures
prune_orphaned_figures = scan_and_prune_orphan_figures
