import shutil
from pathlib import Path


def main():
    workspace_dir = Path(__file__).resolve().parents[1]
    md_dir = workspace_dir / ".md"
    src_dir = md_dir / "legal_docs/luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat"

    if not src_dir.exists():
        print(f"Source directory {src_dir} does not exist.")
        return

    # 1. Define mapping from old slugs to new ISO names
    mapping = {
        # Primary Law
        "luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat": "CCBA_RD_VBPL_001_Rev00-L_135_2025",
        # Guiding Documents
        "nghi_dinh_217_2026_nd_cp_huong_dan_luat_xay_dung_quan_ly_hoat_dong_xay_dung_moi_nhat": "CCBA_RD_VBPL_002_Rev00-ND_217_2026",
        "nghi_dinh_212_2026_nd_cp_dieu_kien_nang_luc_hoat_dong_xay_dung_moi_nhat": "CCBA_RD_VBPL_003_Rev00-ND_212_2026",
        "nghi_dinh_209_2026_nd_cp_huong_dan_luat_xay_dung_ve_quan_ly_vat_lieu_xay_dung_moi_nhat": "CCBA_RD_VBPL_004_Rev00-ND_209_2026",
        "nghi_dinh_207_2026_nd_cp_huong_dan_luat_xay_dung_quan_ly_chat_luong_thi_cong_xay_dung_moi_nhat": "CCBA_RD_VBPL_005_Rev00-ND_207_2026",
        "nghi_dinh_206_2026_nd_cp_huong_dan_quan_ly_chi_phi_dau_tu_xay_dung_moi_nhat": "CCBA_RD_VBPL_006_Rev00-ND_206_2026",
        "nghi_dinh_193_2026_nd_cp_quyet_toan_von_dau_tu_du_an_moi_nhat": "CCBA_RD_VBPL_007_Rev00-ND_193_2026",
        "thong_tu_34_2026_tt_bxd_cap_cong_trinh_xay_dung_phuc_vu_quan_ly_hoat_dong_xay_dung_moi_nhat": "CCBA_RD_VBPL_008_Rev00-TT_34_2026",
    }

    # Helper mappings for checklist, index, and relationship
    other_mappings = {
        "compliance_checklist": "CCBA_RD_VBPL_001_Rev00-L_135_2025-Checklist",
        "index": "CCBA_RD_VBPL_001_Rev00-L_135_2025-Index",
        "relationship_chart": "CCBA_RD_VBPL_001_Rev00-L_135_2025-Relationship",
    }

    print("--- Standardizing legal documents to ISO conventions ---")

    # 2. Read, update, and move files to .md/
    all_moved_files = []

    # Primary files
    primary_files = [
        (
            "luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat.md",
            "CCBA_RD_VBPL_001_Rev00-L_135_2025.md",
        ),
        (
            "luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat.docx",
            "CCBA_RD_VBPL_001_Rev00-L_135_2025.docx",
        ),
        ("compliance_checklist.md", "CCBA_RD_VBPL_001_Rev00-L_135_2025-Checklist.md"),
        ("index.md", "CCBA_RD_VBPL_001_Rev00-L_135_2025-Index.md"),
        ("relationship_chart.md", "CCBA_RD_VBPL_001_Rev00-L_135_2025-Relationship.md"),
    ]

    for old_name, new_name in primary_files:
        old_path = src_dir / old_name
        new_path = md_dir / new_name
        if old_path.exists():
            if old_path.suffix == ".md":
                content = old_path.read_text(encoding="utf-8")
                # Replace links
                for old_slug, new_iso in mapping.items():
                    content = content.replace(f"guiding_docs/{old_slug}.md", f"{new_iso}.md")
                    content = content.replace(f"{old_slug}.md", f"{new_iso}.md")
                for old_slug, new_iso in other_mappings.items():
                    content = content.replace(f"{old_slug}.md", f"{new_iso}.md")
                new_path.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(old_path, new_path)
            print(f"Moved: {old_name} -> {new_name}")
            all_moved_files.append(new_path)

    # Guiding files
    for old_slug, new_iso in mapping.items():
        if old_slug == "luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat":
            continue

        # md file
        old_md = src_dir / f"guiding_docs/{old_slug}.md"
        new_md = md_dir / f"{new_iso}.md"
        if old_md.exists():
            content = old_md.read_text(encoding="utf-8")
            for o_slug, n_iso in mapping.items():
                content = content.replace(f"guiding_docs/{o_slug}.md", f"{n_iso}.md")
                content = content.replace(f"{o_slug}.md", f"{n_iso}.md")
            new_md.write_text(content, encoding="utf-8")
            print(f"Moved guiding md: {old_slug}.md -> {new_iso}.md")
            all_moved_files.append(new_md)

        # docx file
        old_docx = src_dir / f"guiding_docs/{old_slug}.docx"
        new_docx = md_dir / f"{new_iso}.docx"
        if old_docx.exists():
            shutil.copy2(old_docx, new_docx)
            print(f"Moved guiding docx: {old_slug}.docx -> {new_iso}.docx")
            all_moved_files.append(new_docx)

    # 3. Clean up old folders
    print("\n--- Cleaning up temporary directories ---")
    try:
        shutil.rmtree(md_dir / "legal_docs")
        print("Removed .md/legal_docs directory.")
    except Exception as e:
        print(f"Error removing .md/legal_docs: {e}")

    try:
        shutil.rmtree(md_dir / "test_active_download", ignore_errors=True)
        shutil.rmtree(md_dir / "test_download", ignore_errors=True)
        print("Removed temporary test_download directories.")
    except Exception as e:
        print(f"Error removing test directories: {e}")

    print("\nStandardization finished successfully!")


if __name__ == "__main__":
    main()
