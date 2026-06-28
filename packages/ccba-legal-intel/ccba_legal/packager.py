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
                print(f"[OKF Packager] Moved guiding MD: {gf}.md -> legal_docs/{bundle_slug}/guiding_docs/{gf}.md")

            old_docx = md_dir / f"{gf}.docx"
            new_docx = guiding_dir / f"{gf}.docx"
            if old_docx.exists():
                shutil.move(old_docx, new_docx)
                print(f"[OKF Packager] Moved guiding DOCX: {gf}.docx -> legal_docs/{bundle_slug}/guiding_docs/{gf}.docx")


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
