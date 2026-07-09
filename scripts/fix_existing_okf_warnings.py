#!/usr/bin/env python3
"""fix_existing_okf_warnings.py - Migration script to fix OKF warnings in the bundle.

Updates frontmatter metadata, resolves relative cross-links into bundle-absolute paths,
and adds missing circular documents to index.md.
"""

import re
from pathlib import Path
from typing import Any

import yaml

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_ROOT = PROJECT_ROOT / ".md" / "legal_docs" / "luat_xay_dung_2025_so_135_2025_qh15"
REGISTRY_PATH = PROJECT_ROOT / ".md" / "data" / "legal_registry.yaml"


def load_registry_map() -> dict[str, dict[str, Any]]:
    """Load registry mappings from legal_registry.yaml.

    Returns:
        A dictionary mapping lowercase filename to its registry document entry.
    """
    if not REGISTRY_PATH.exists():
        print(f"Registry path not found at {REGISTRY_PATH}")
        return {}

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = yaml.safe_load(f) or {}

    doc_map = {}
    for _, docs in registry.items():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            paths = []
            if "markdown_path" in doc:
                paths.append(doc["markdown_path"])
            if "file_path" in doc:
                fp = doc["file_path"]
                paths.append(fp)
                if fp.endswith(".docx"):
                    paths.append(fp[:-5] + ".md")

            for p in paths:
                filename = p.replace("\\", "/").split("/")[-1].lower()
                doc_map[filename] = doc
    return doc_map


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return (frontmatter_dict, remaining_content).

    Args:
        content: File contents.

    Returns:
        A tuple of (parsed_frontmatter, remaining_body).
    """
    stripped = content.strip()
    if not stripped.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) >= 3:
        try:
            fm = yaml.safe_load(parts[1])
            if isinstance(fm, dict):
                return fm, parts[2]
        except Exception:
            pass
    return {}, content


def write_file_with_frontmatter(file_path: Path, fm: dict[str, Any], body: str) -> None:
    """Write frontmatter and body back to a file.

    Args:
        file_path: Path to the target file.
        fm: Frontmatter dictionary.
        body: Body of the markdown document.
    """
    fm_text = yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False)
    new_content = f"---\n{fm_text}---\n{body.lstrip()}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def determine_type(filename: str, current_type: str | None) -> str:
    """Determine OKF type based on filename and current type.

    Args:
        filename: Filename.
        current_type: Existing type field in frontmatter.

    Returns:
        Approved OKF type string.
    """
    allowed = {
        "Law",
        "Decree",
        "Circular",
        "Standard",
        "Appendix",
        "Section",
        "Consolidated Document",
        "Guiding Document",
    }
    if current_type in allowed:
        return current_type
    fn = filename.lower()
    if "luat_" in fn:
        return "Law"
    if "nghi_dinh_" in fn:
        return "Decree"
    if "thong_tu_" in fn:
        return "Circular"
    return "Guiding Document"


def pass1_update_main_and_bundle_docs(doc_map: dict[str, dict[str, Any]]) -> None:
    """Pass 1: Update metadata for main documents and bundle-level files.

    Args:
        doc_map: Map of filename to registry entries.
    """
    print("Pass 1: Updating main documents and bundle-level files...")
    bundle_files = {
        "index.md": {
            "type": "Guiding Document",
            "resource": "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Luat-Xay-dung-2025-so-135-2025-QH15-675213.aspx",
            "status": "current",
            "timestamp": "2026-06-28T04:07:29Z",
        },
        "compliance_checklist.md": {
            "type": "Guiding Document",
            "resource": "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Luat-Xay-dung-2025-so-135-2025-QH15-675213.aspx",
            "status": "current",
            "timestamp": "2026-06-28T04:05:16Z",
        },
        "relationship_chart.md": {
            "type": "Guiding Document",
            "resource": "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Luat-Xay-dung-2025-so-135-2025-QH15-675213.aspx",
            "status": "current",
            "timestamp": "2026-06-28T04:07:29Z",
        },
    }

    for fname, updates in bundle_files.items():
        fpath = BUNDLE_ROOT / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            fm, body = parse_frontmatter(content)
            fm.update(updates)
            write_file_with_frontmatter(fpath, fm, body)
            print(f"  Updated bundle-level file: {fname}")

    for p in BUNDLE_ROOT.rglob("*.md"):
        if "appendices" in p.parts or p.name in bundle_files:
            continue

        with open(p, encoding="utf-8") as f:
            content = f.read()
        fm, body = parse_frontmatter(content)
        doc = doc_map.get(p.name.lower())
        if doc:
            fm["resource"] = doc.get("download_url", "")
            fm["status"] = doc.get("status", "current")
            fm["document_number"] = doc.get("document_number", "")
            issued_date = doc.get("issued_date")
            fm["timestamp"] = f"{issued_date}T00:00:00Z" if issued_date else "2026-07-05T12:00:00Z"
            fm["type"] = determine_type(p.name, fm.get("type"))
            write_file_with_frontmatter(p, fm, body)
            print(f"  Updated parent document: {p.relative_to(BUNDLE_ROOT)}")


def pass2_update_appendix_files() -> None:
    """Pass 2: Inherit metadata for appendix documents from parents."""
    print("Pass 2: Inheriting metadata for appendix documents...")
    appendices_dir = BUNDLE_ROOT / "guiding_docs" / "appendices"
    if not appendices_dir.exists():
        return

    for p in appendices_dir.glob("*.md"):
        with open(p, encoding="utf-8") as f:
            content = f.read()
        fm, body = parse_frontmatter(content)

        parent_rel = fm.get("parent_document")
        if parent_rel:
            parent_path = (p.parent / parent_rel).resolve()
            if parent_path.exists():
                with open(parent_path, encoding="utf-8") as f_parent:
                    parent_content = f_parent.read()
                parent_fm, _ = parse_frontmatter(parent_content)

                fm["resource"] = parent_fm.get("resource", "")
                fm["status"] = parent_fm.get("status", "current")
                fm["document_number"] = parent_fm.get("document_number", "")
                fm["timestamp"] = parent_fm.get("timestamp", "2026-07-05T12:00:00Z")
                fm["type"] = "Appendix"

                write_file_with_frontmatter(p, fm, body)
                print(f"  Updated appendix: {p.name}")
            else:
                print(f"  [ERROR] Parent path not found for {p.name}: {parent_path}")


def pass3_register_orphans_in_index() -> None:
    """Pass 3: Programmatically add Thông tư 36 and 37 to index.md."""
    print("Pass 3: Registering missing circulars in index.md...")
    index_path = BUNDLE_ROOT / "index.md"
    if not index_path.exists():
        print(f"Error: index.md not found at {index_path}")
        return

    with open(index_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    has_tt36 = any("thong_tu_36" in line for line in lines)
    has_tt37 = any("thong_tu_37" in line for line in lines)
    if not (has_tt36 and has_tt37):
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if "- [Thông tư 34/2026/TT-BXD" in line and "thong_tu_34" in line:
                new_lines.append(
                    "- [Thông tư 36/2026/TT-BXD (Hướng dẫn phương pháp xác định và quản lý chi phí đầu"
                    " tư xây dựng)](guiding_docs/thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh"
                    "_va_qu.md) (type: `Circular`)"
                )
                new_lines.append(
                    "- [Thông tư 37/2026/TT-BXD (Phương pháp xác định định mức dự toán)](guiding_docs/"
                    "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa.md) (type: `Circular`)"
                )
            elif "thong_tu_34_2026_tt_bxd_cap_cong_trinh_xay_dung-phu_luc_03.md" in line:
                new_lines.extend(
                    [
                        "",
                        "#### Phụ lục Thông tư 36/2026/TT-BXD (Xác định và quản lý chi phí)",
                        "- [PHỤ LỤC I: Mẫu biểu xác định và quản lý chi phí](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_01.md)",
                        "- [PHỤ LỤC II: Mẫu biểu quản lý chi phí đầu tư](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_02.md)",
                        "- [PHỤ LỤC III: Mẫu biểu báo cáo chi phí](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_03.md)",
                        "- [PHỤ LỤC IV: Mẫu biểu dự toán xây dựng](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_04.md)",
                        "- [PHỤ LỤC V: Mẫu biểu chi phí thiết bị](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_05.md)",
                        "- [PHỤ LỤC VI: Mẫu biểu chi phí quản lý dự án](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_06.md)",
                        "- [PHỤ LỤC VII: Mẫu biểu chi phí tư vấn](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_07.md)",
                        "- [PHỤ LỤC VIII: Mẫu biểu chi phí khác](guiding_docs/appendices/"
                        "thong_tu_36_2026_tt_bxd_huong_dan_phuong_phap_xac_dinh_va_qu-phu_luc_08.md)",
                        "",
                        "#### Phụ lục Thông tư 37/2026/TT-BXD (Phương pháp xác định định mức)",
                        "- [PHỤ LỤC I: Phương pháp xác định định mức dự toán](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_01.md)",
                        "- [PHỤ LỤC II: Phương pháp xác định định mức chi phí](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_02.md)",
                        "- [PHỤ LỤC III: Phương pháp xác định hao phí vật liệu](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_03.md)",
                        "- [PHỤ LỤC IV: Phương pháp xác định hao phí nhân công](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_04.md)",
                        "- [PHỤ LỤC V: Phương pháp xác định hao phí máy thi công](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_05.md)",
                        "- [PHỤ LỤC VI: Phương pháp xác định chỉ số giá xây dựng](guiding_docs/appendices/"
                        "thong_tu_37_2026_tt_bxd_phuong_phap_xac_dinh_dinh_muc_du_toa-phu_luc_06.md)",
                    ]
                )
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        print("  Successfully updated index.md.")
    else:
        print("  Circulars already registered in index.md.")

    # Always remove backticks around types in index.md to prevent code reference linter warnings
    with open(index_path, encoding="utf-8") as f:
        idx_content = f.read()

    idx_content = idx_content.replace("(type: `Law`)", "(type: Law)")
    idx_content = idx_content.replace("(type: `Decree`)", "(type: Decree)")
    idx_content = idx_content.replace("(type: `Decision`)", "(type: Decision)")
    idx_content = idx_content.replace("(type: `Circular`)", "(type: Circular)")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(idx_content)
    print("  Removed type backticks in index.md.")


def convert_markdown_links(content: str, file_path: Path) -> tuple[str, bool]:
    """Convert relative links to absolute bundle-relative links.

    Args:
        content: The input file content.
        file_path: The Path of the current file being processed.

    Returns:
        A tuple of (new_content, was_modified).
    """
    modified = False

    def repl(match: re.Match) -> str:
        nonlocal modified
        text = match.group(1)
        href = match.group(2)

        if href.startswith(("http", "#", "mailto:")):
            return match.group(0)

        parts = href.split("#", 1)
        base_href = parts[0]
        anchor = parts[1] if len(parts) > 1 else ""

        if base_href.startswith("/"):
            norm_base = base_href.replace("\\", "/")
            new_href = norm_base + (f"#{anchor}" if anchor else "")
            if new_href != href:
                modified = True
            return f"[{text}]({new_href})"

        try:
            target_path = (file_path.parent / base_href).resolve()
            if target_path.is_relative_to(BUNDLE_ROOT):
                rel_path = target_path.relative_to(BUNDLE_ROOT).as_posix()
                new_href = "/" + rel_path
                if anchor:
                    new_href += f"#{anchor}"
                modified = True
                return f"[{text}]({new_href})"
        except Exception:
            pass

        return match.group(0)

    new_content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, content)
    return new_content, modified


def pass4_convert_links_to_absolute() -> None:
    """Pass 4: Convert relative internal cross-links to bundle-absolute paths."""
    print("Pass 4: Converting cross-links to bundle-absolute paths...")

    for p in BUNDLE_ROOT.rglob("*.md"):
        with open(p, encoding="utf-8") as f:
            content = f.read()

        new_content, modified = convert_markdown_links(content, p)

        if modified:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  Converted links in: {p.relative_to(BUNDLE_ROOT)}")


def main() -> None:
    """Run all passes of the OKF warning fix migration."""
    print(f"Starting OKF Warning Fix Migration in bundle: {BUNDLE_ROOT.name}")
    doc_map = load_registry_map()

    pass1_update_main_and_bundle_docs(doc_map)
    pass2_update_appendix_files()
    pass3_register_orphans_in_index()
    pass4_convert_links_to_absolute()

    print("\nMigration completed successfully!")


if __name__ == "__main__":
    main()
