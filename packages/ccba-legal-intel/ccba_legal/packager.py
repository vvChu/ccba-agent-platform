import re
import shutil
import time
from pathlib import Path


class OKFBundlePackager:
    """Manages creation, writing, and directory structure organization of Open Knowledge Format (OKF) Bundles."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def sanitize_slug(self, text: str) -> str:
        """Create a clean directory slug from URL or title."""
        text = text.lower()
        # Replace slashes and dots with spaces
        text = text.replace('/', ' ').replace('\\', ' ').replace('.', ' ')
        # Remove accents
        accents = {
            'a': 'áàảãạăắằẳẵặâấầẩẫậ',
            'd': 'đ',
            'e': 'éèẻẽẹêếềểễệ',
            'i': 'íìỉĩị',
            'o': 'óòỏõọôốồổỗộơớờởỡợ',
            'u': 'úùủũụưứừửữự',
            'y': 'ýỳỷỹỵ'
        }
        for char, group in accents.items():
            for g in group:
                text = text.replace(g, char)
        text = re.sub(r'[^a-z0-9\s_-]', '', text)
        text = re.sub(r'[\s_-]+', '_', text).strip('_')
        return text

    def write_concept(self, relative_path: str, concept_type: str, title: str,
                      description: str, content: str, resource_uri: str = "") -> None:
        """Write a concept file with valid OKF YAML frontmatter."""
        dest = self.root_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = f"""---
type: {concept_type}
title: "{title}"
description: "{description}"
resource: "{resource_uri}"
timestamp: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
---

{content}
"""
        with open(dest, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        print(f"[OKF Packager] Wrote concept to {dest}")

    def organize_bundle_structure(self, bundle_slug: str, guiding_files: list[str]) -> None:
        """Move generated primary and guiding files into an isolated OKF Bundle directory under legal_docs/."""
        md_dir = self.root_dir
        bundle_dir = md_dir / "legal_docs" / bundle_slug
        guiding_dir = bundle_dir / "guiding_docs"

        # Create target directories
        guiding_dir.mkdir(parents=True, exist_ok=True)

        primary_files = {
            f"{bundle_slug}.md": f"{bundle_slug}.md",
            f"{bundle_slug}.docx": f"{bundle_slug}.docx",
            "index.md": "index.md",
            "compliance_checklist.md": "compliance_checklist.md",
            "relationship_chart.md": "relationship_chart.md",
            "diff_report.md": "diff_report.md"
        }

        # 1. Move primary files and rewrite content links
        all_app_paths = []
        for old_name, new_name in primary_files.items():
            old_path = md_dir / old_name
            new_path = bundle_dir / new_name

            if old_path.exists():
                if old_path.suffix == ".md":
                    content = old_path.read_text(encoding="utf-8")

                    # Update guiding document links to point into guiding_docs/
                    for gf in guiding_files:
                        content = content.replace(f"{gf}.md", f"guiding_docs/{gf}.md")

                    new_path.write_text(content, encoding="utf-8")
                    old_path.unlink()

                    # Split appendices if any
                    apps = self.split_concept_appendices(new_path)
                    for ap in apps:
                        all_app_paths.append((new_name.replace(".md", ""), ap))
                else:
                    shutil.move(old_path, new_path)
                print(f"[OKF Packager] Moved primary file: {old_name} -> legal_docs/{bundle_slug}/{new_name}")

        # 2. Move guiding documents and rewrite content links
        for gf in guiding_files:
            old_md = md_dir / f"{gf}.md"
            new_md = guiding_dir / f"{gf}.md"
            if old_md.exists():
                content = old_md.read_text(encoding="utf-8")

                # Update links pointing to primary law and support documents (up one level)
                content = content.replace(f"{bundle_slug}.md", f"../{bundle_slug}.md")
                content = content.replace("index.md", "../index.md")
                content = content.replace("compliance_checklist.md", "../compliance_checklist.md")
                content = content.replace("relationship_chart.md", "../relationship_chart.md")
                content = content.replace("diff_report.md", "../diff_report.md")

                new_md.write_text(content, encoding="utf-8")
                old_md.unlink()

                # Split appendices if any
                apps = self.split_concept_appendices(new_md)
                for ap in apps:
                    all_app_paths.append((gf, f"guiding_docs/{ap}"))
                print(f"[OKF Packager] Moved guiding MD: {gf}.md -> legal_docs/{bundle_slug}/guiding_docs/{gf}.md")

            old_docx = md_dir / f"{gf}.docx"
            new_docx = guiding_dir / f"{gf}.docx"
            if old_docx.exists():
                shutil.move(old_docx, new_docx)
                print(f"[OKF Packager] Moved guiding DOCX: {gf}.docx -> legal_docs/{bundle_slug}/guiding_docs/{gf}.docx")

        # 3. Update index.md with appendices
        index_path = bundle_dir / "index.md"
        if index_path.exists() and all_app_paths:
            index_content = index_path.read_text(encoding="utf-8")
            if "### Phụ lục đính kèm" not in index_content:
                appendix_section = "\n### Phụ lục đính kèm (Decree Appendices)\n\n"
                for _parent, rel_link in all_app_paths:
                    filename = rel_link.split("/")[-1]
                    label = filename.replace(".md", "").replace("_", " ").title()
                    # Make Roman numerals uppercase in the label
                    label = re.sub(r'\bPhu Luc (\d+)\b', lambda m: f"Phụ lục {m.group(1)}", label, flags=re.IGNORECASE)
                    appendix_section += f"- [{label}]({rel_link})\n"

                index_path.write_text(index_content.strip() + "\n" + appendix_section, encoding="utf-8")
                print("[OKF Packager] Updated index.md with split appendices list.")

    def split_concept_appendices(self, file_path: Path) -> list[str]:
        """Detect and split appendices from a markdown file, saving them in an appendices/ subdirectory."""
        if not file_path.exists():
            return []

        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        pattern = re.compile(r"^#*\s*(PHỤ LỤC\s+([IVXLCDM]+))\s*$", re.IGNORECASE)
        matches = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                roman = m.group(2)
                matches.append((idx, m.group(1), roman))

        if not matches:
            return []

        parent_slug = file_path.stem
        parent_dir = file_path.parent
        appendices_dir = parent_dir / "appendices"
        appendices_dir.mkdir(parents=True, exist_ok=True)

        main_body_lines = lines[:matches[0][0]]
        while main_body_lines and not main_body_lines[-1].strip():
            main_body_lines.pop()

        def roman_to_decimal(r: str) -> int:
            r = r.upper()
            roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
            val = 0
            for i in range(len(r)):
                if i > 0 and roman_map[r[i]] > roman_map[r[i-1]]:
                    val += roman_map[r[i]] - 2 * roman_map[r[i-1]]
                else:
                    val += roman_map[r[i]]
            return val

        appendix_links = []
        for i, (idx, full_label, roman) in enumerate(matches):
            start_idx = idx
            end_idx = matches[i+1][0] if i + 1 < len(matches) else len(lines)

            app_lines = lines[start_idx:end_idx]
            app_lines.pop(0)  # remove header line

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

            frontmatter = f"""---
type: Appendix
title: "{full_label} - {title}"
description: "Chi tiết {full_label} ban hành kèm theo {parent_slug.replace('_', ' ').title()}"
parent_document: "../{file_path.name}"
uniclass: "Fi_10_20"
---

# {full_label}

"""
            app_content = frontmatter + "\n".join(app_lines).strip() + "\n"
            app_path.write_text(app_content, encoding="utf-8")

            appendix_links.append(f"- [{full_label}: {title}](appendices/{app_filename})")

        new_parent_content = "\n".join(main_body_lines).strip() + "\n\n"
        new_parent_content += "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM\n\n"
        new_parent_content += "\n".join(appendix_links) + "\n"

        file_path.write_text(new_parent_content, encoding="utf-8")
        return [f"appendices/{parent_slug}-phu_luc_{f'{roman_to_decimal(m[2]):02d}'}.md" for m in matches]


def is_guiding_link(url: str) -> bool:
    """Check if the URL points to a guiding or related document (including VBHN)."""
    url_lower = url.lower()
    keywords = ["nghi-dinh", "thong-tu", "quyet-dinh", "cong-van", "van-ban-hop-nhat", "vbhn"]
    return any(k in url_lower for k in keywords)


def get_concept_type(url: str) -> str:
    """Map a URL to its corresponding OKF concept type."""
    url_lower = url.lower()
    if "nghi-dinh" in url_lower:
        return "Decree"
    if "thong-tu" in url_lower:
        return "Circular"
    if "quyet-dinh" in url_lower:
        return "Decision"
    if "cong-van" in url_lower:
        return "Official Letter"
    if "van-ban-hop-nhat" in url_lower or "vbhn" in url_lower:
        return "Consolidated Document"
    return "Guiding Document"
