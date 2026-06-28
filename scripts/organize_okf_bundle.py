import shutil
from pathlib import Path


def main():
    workspace_dir = Path("d:/GitHubProjects/ccba-agent-platform")
    md_dir = workspace_dir / ".md"
    bundle_slug = "luat_xay_dung_2025_so_135_2025_qh15"
    bundle_dir = md_dir / "legal_docs" / bundle_slug
    guiding_dir = bundle_dir / "guiding_docs"

    # Create target directories
    guiding_dir.mkdir(parents=True, exist_ok=True)

    # 1. Primary files mapping (Source under .md/ -> Destination under bundle_dir)
    primary_files = {
        f"{bundle_slug}.md": f"{bundle_slug}.md",
        f"{bundle_slug}.docx": f"{bundle_slug}.docx",
        f"{bundle_slug}-Index.md": "index.md",
        f"{bundle_slug}-Checklist.md": "compliance_checklist.md",
        f"{bundle_slug}-Relationship.md": "relationship_chart.md",
    }

    # 2. Guiding files list
    guiding_files = [
        "nghi_dinh_217_2026_nd_cp_quan_ly_hoat_dong_xay_dung",
        "nghi_dinh_212_2026_nd_cp_dieu_kien_nang_luc_hoat_dong_xay_dung",
        "nghi_dinh_209_2026_nd_cp_quan_ly_vat_lieu_xay_dung",
        "nghi_dinh_207_2026_nd_cp_quan_ly_chat_luong_thi_cong_xay_dung",
        "nghi_dinh_206_2026_nd_cp_quan_ly_chi_phi_dau_tu_xay_dung",
        "nghi_dinh_193_2026_nd_cp_quyet_toan_von_dau_tu_du_an",
        "thong_tu_34_2026_tt_bxd_cap_cong_trinh_xay_dung"
    ]

    print("--- Organizing OKF Bundle in legal_docs directory ---")

    # Move primary files and rewrite content links
    for old_name, new_name in primary_files.items():
        old_path = md_dir / old_name
        new_path = bundle_dir / new_name

        if old_path.exists():
            if old_path.suffix == ".md":
                content = old_path.read_text(encoding="utf-8")

                # Update support file links to their new names
                content = content.replace(f"{bundle_slug}-Checklist.md", "compliance_checklist.md")
                content = content.replace(f"{bundle_slug}-Index.md", "index.md")
                content = content.replace(f"{bundle_slug}-Relationship.md", "relationship_chart.md")

                # Update guiding document links to point into guiding_docs/
                for gf in guiding_files:
                    content = content.replace(f"{gf}.md", f"guiding_docs/{gf}.md")

                new_path.write_text(content, encoding="utf-8")
                old_path.unlink()
            else:
                shutil.move(old_path, new_path)
            print(f"Moved primary file: {old_name} -> legal_docs/{bundle_slug}/{new_name}")

    # Move guiding documents and rewrite content links
    for gf in guiding_files:
        # Move MD
        old_md = md_dir / f"{gf}.md"
        new_md = guiding_dir / f"{gf}.md"
        if old_md.exists():
            content = old_md.read_text(encoding="utf-8")

            # Update links inside guiding documents:
            # - Primary Law is one level up: ../luat_xay_dung_2025_so_135_2025_qh15.md
            # - Support files are one level up: ../index.md, etc.
            content = content.replace(f"{bundle_slug}.md", f"../{bundle_slug}.md")
            content = content.replace(f"{bundle_slug}-Index.md", "../index.md")
            content = content.replace(f"{bundle_slug}-Checklist.md", "../compliance_checklist.md")
            content = content.replace(f"{bundle_slug}-Relationship.md", "../relationship_chart.md")

            new_md.write_text(content, encoding="utf-8")
            old_md.unlink()
            print(f"Moved guiding MD: {gf}.md -> legal_docs/{bundle_slug}/guiding_docs/{gf}.md")

        # Move DOCX
        old_docx = md_dir / f"{gf}.docx"
        new_docx = guiding_dir / f"{gf}.docx"
        if old_docx.exists():
            shutil.move(old_docx, new_docx)
            print(f"Moved guiding DOCX: {gf}.docx -> legal_docs/{bundle_slug}/guiding_docs/{gf}.docx")

    print("\nOKF Bundle successfully organized and ready for LLM Agents!")

if __name__ == "__main__":
    main()
