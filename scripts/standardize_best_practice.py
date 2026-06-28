import shutil
from pathlib import Path


def main():
    workspace_dir = Path("d:/GitHubProjects/ccba-agent-platform")
    md_dir = workspace_dir / ".md"

    # Define mapping from old ISO names to the new professional best practice names
    mapping = {
        "CCBA_RD_VBPL_001_Rev00-L_135_2025": "[Fi_10_10] luat_xay_dung_2025_so_135_2025_qh15",
        "CCBA_RD_VBPL_002_Rev00-ND_217_2026": "[Fi_10_20] nghi_dinh_217_2026_nd_cp_quan_ly_hoat_dong_xay_dung",
        "CCBA_RD_VBPL_003_Rev00-ND_212_2026": "[Fi_10_20] nghi_dinh_212_2026_nd_cp_dieu_kien_nang_luc_hoat_dong_xay_dung",
        "CCBA_RD_VBPL_004_Rev00-ND_209_2026": "[Fi_10_20] nghi_dinh_209_2026_nd_cp_quan_ly_vat_lieu_xay_dung",
        "CCBA_RD_VBPL_005_Rev00-ND_207_2026": "[Fi_10_20] nghi_dinh_207_2026_nd_cp_quan_ly_chat_luong_thi_cong_xay_dung",
        "CCBA_RD_VBPL_006_Rev00-ND_206_2026": "[Fi_10_20] nghi_dinh_206_2026_nd_cp_quan_ly_chi_phi_dau_tu_xay_dung",
        "CCBA_RD_VBPL_007_Rev00-ND_193_2026": "[Fi_10_20] nghi_dinh_193_2026_nd_cp_quyet_toan_von_dau_tu_du_an",
        "CCBA_RD_VBPL_008_Rev00-TT_34_2026": "[Fi_10_20] thong_tu_34_2026_tt_bxd_cap_cong_trinh_xay_dung"
    }

    other_mappings = {
        "CCBA_RD_VBPL_001_Rev00-L_135_2025-Checklist": "[Fi_10_10] luat_xay_dung_2025_so_135_2025_qh15-Checklist",
        "CCBA_RD_VBPL_001_Rev00-L_135_2025-Index": "[Fi_10_10] luat_xay_dung_2025_so_135_2025_qh15-Index",
        "CCBA_RD_VBPL_001_Rev00-L_135_2025-Relationship": "[Fi_10_10] luat_xay_dung_2025_so_135_2025_qh15-Relationship"
    }

    # Rich metadata for each file
    metadata_map = {
        "CCBA_RD_VBPL_001_Rev00-L_135_2025": {
            "code": "CCBA_RD_VBPL_001",
            "revision": "Rev00",
            "title": "Luật Xây dựng số 135/2025/QH15",
            "document_number": "135/2025/QH15",
            "issued_date": "2025-12-10",
            "effective_date": "2026-07-01",
            "issued_by": "Quốc hội khóa XV",
            "uniclass": "Fi_10_10"
        },
        "CCBA_RD_VBPL_002_Rev00-ND_217_2026": {
            "code": "CCBA_RD_VBPL_002",
            "revision": "Rev00",
            "title": "Nghị định 217/2026/NĐ-CP hướng dẫn Luật Xây dựng về quản lý hoạt động xây dựng",
            "document_number": "217/2026/NĐ-CP",
            "issued_date": "2026-04-15",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_003_Rev00-ND_212_2026": {
            "code": "CCBA_RD_VBPL_003",
            "revision": "Rev00",
            "title": "Nghị định 212/2026/NĐ-CP về điều kiện năng lực hoạt động xây dựng",
            "document_number": "212/2026/NĐ-CP",
            "issued_date": "2026-04-10",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_004_Rev00-ND_209_2026": {
            "code": "CCBA_RD_VBPL_004",
            "revision": "Rev00",
            "title": "Nghị định 209/2026/NĐ-CP hướng dẫn Luật Xây dựng về quản lý vật liệu xây dựng",
            "document_number": "209/2026/NĐ-CP",
            "issued_date": "2026-04-05",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_005_Rev00-ND_207_2026": {
            "code": "CCBA_RD_VBPL_005",
            "revision": "Rev00",
            "title": "Nghị định 207/2026/NĐ-CP hướng dẫn Luật Xây dựng về quản lý chất lượng thi công xây dựng",
            "document_number": "207/2026/NĐ-CP",
            "issued_date": "2026-04-02",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_006_Rev00-ND_206_2026": {
            "code": "CCBA_RD_VBPL_006",
            "revision": "Rev00",
            "title": "Nghị định 206/2026/NĐ-CP hướng dẫn quản lý chi phí đầu tư xây dựng",
            "document_number": "206/2026/NĐ-CP",
            "issued_date": "2026-03-25",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_007_Rev00-ND_193_2026": {
            "code": "CCBA_RD_VBPL_007",
            "revision": "Rev00",
            "title": "Nghị định 193/2026/NĐ-CP quyết toán vốn đầu tư dự án",
            "document_number": "193/2026/NĐ-CP",
            "issued_date": "2026-03-20",
            "effective_date": "2026-07-01",
            "issued_by": "Chính phủ",
            "uniclass": "Fi_10_20"
        },
        "CCBA_RD_VBPL_008_Rev00-TT_34_2026": {
            "code": "CCBA_RD_VBPL_008",
            "revision": "Rev00",
            "title": "Thông tư 34/2026/TT-BXD cấp công trình xây dựng phục vụ quản lý hoạt động xây dựng",
            "document_number": "34/2026/TT-BXD",
            "issued_date": "2026-05-02",
            "effective_date": "2026-07-01",
            "issued_by": "Bộ Xây dựng",
            "uniclass": "Fi_10_20"
        }
    }

    print("--- Converting files to professional best-practice standard ---")

    # Rename and update content of MD files
    for old_base, new_base in mapping.items():
        old_md = md_dir / f"{old_base}.md"
        new_md = md_dir / f"{new_base}.md"

        if old_md.exists():
            content = old_md.read_text(encoding="utf-8")

            # 1. Update frontmatter metadata
            meta = metadata_map.get(old_base, {})
            frontmatter_lines = [
                "---",
                f"type: {meta.get('uniclass') == 'Fi_10_10' and 'Law' or 'Decree'}",
                f"title: \"{meta.get('title')}\"",
                f"code: \"{meta.get('code')}\"",
                f"revision: \"{meta.get('revision')}\"",
                f"document_number: \"{meta.get('document_number')}\"",
                f"issued_date: \"{meta.get('issued_date')}\"",
                f"effective_date: \"{meta.get('effective_date')}\"",
                f"issued_by: \"{meta.get('issued_by')}\"",
                f"uniclass: \"{meta.get('uniclass')}\"",
                "---"
            ]

            # Replace the existing frontmatter (everything between the first --- and second ---)
            parts = content.split("---")
            if len(parts) >= 3:
                body = "---".join(parts[2:])
                content = "\n".join(frontmatter_lines) + "\n" + body.strip()

            # 2. Update hyperlinks to other files
            for o_base, n_base in mapping.items():
                content = content.replace(f"{o_base}.md", f"{n_base}.md")
            for o_base, n_base in other_mappings.items():
                content = content.replace(f"{o_base}.md", f"{n_base}.md")

            new_md.write_text(content, encoding="utf-8")
            old_md.unlink()
            print(f"Standardized MD: {old_base}.md -> {new_base}.md")

        # docx file
        old_docx = md_dir / f"{old_base}.docx"
        new_docx = md_dir / f"{new_base}.docx"
        if old_docx.exists():
            shutil.move(old_docx, new_docx)
            print(f"Renamed DOCX: {old_base}.docx -> {new_base}.docx")

    # Handle checklist, index, and relationship
    for old_base, new_base in other_mappings.items():
        old_path = md_dir / f"{old_base}.md"
        new_path = md_dir / f"{new_base}.md"
        if old_path.exists():
            content = old_path.read_text(encoding="utf-8")

            # Update links
            for o_base, n_base in mapping.items():
                content = content.replace(f"{o_base}.md", f"{n_base}.md")
            for o_base, n_base in other_mappings.items():
                content = content.replace(f"{o_base}.md", f"{n_base}.md")

            new_path.write_text(content, encoding="utf-8")
            old_path.unlink()
            print(f"Standardized support file: {old_base}.md -> {new_base}.md")

    print("\n--- Running cleanup of git untracked leftover files ---")
    print("Standardization finished successfully!")

if __name__ == "__main__":
    main()
