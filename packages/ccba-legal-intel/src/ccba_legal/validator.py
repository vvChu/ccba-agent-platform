"""Validator module for OKF v2.2 legal knowledge bundles and Spoke integrity."""

from __future__ import annotations

import re
from pathlib import Path


def validate_template_and_table_integrity(
    spoke_root: Path,
) -> tuple[list[str], list[str]]:
    """Gate 8: Template & Table Structural Integrity Validator according to ADR 0021."""
    errors: list[str] = []
    warnings: list[str] = []

    legal_docs = spoke_root / "legal_docs"
    if not legal_docs.exists():
        return (errors, warnings)

    for cat_dir in legal_docs.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        for doc_dir in cat_dir.iterdir():
            if not doc_dir.is_dir() or doc_dir.name.startswith("."):
                continue

            primary_md = doc_dir / f"{doc_dir.name}.md"
            if not primary_md.exists():
                continue

            content = primary_md.read_text(encoding="utf-8")
            body_only = content.split("## 📑")[0] if "## 📑" in content else content
            templates_dir = doc_dir / "templates"

            # Check 1: Missing templates when forms are defined in normative body
            form_regex = re.compile(
                r"(?:Mẫu\s+số\s+[0-9a-zA-Z\.\-]+(?:\s+ban\s+hành)?\s+kèm\s+theo\s+(?:Nghị\s+định|Thông\s+tư|Quyết\s+định)\s+này|"
                r"ban\s+hành\s+kèm\s+theo\s+(?:Nghị\s+định|Thông\s+tư|Quyết\s+định)\s+này\s+(?:các\s+)?(?:mẫu\s+biểu|biểu\s+mẫu)|"
                r"tại\s+Phụ\s+lục\s+Hệ\s+thống\s+biểu\s+mẫu)",
                re.IGNORECASE,
            )
            has_form_definition = bool(form_regex.search(body_only))

            if has_form_definition:
                if not templates_dir.exists() or not list(templates_dir.rglob("*.md")):
                    errors.append(
                        f"Template Integrity Error [{doc_dir.name}]: Document defines form templates, but templates/ is empty or missing."
                    )

            # Check 2: Broken table paragraphs in templates
            if templates_dir.exists():
                for tmpl_file in templates_dir.rglob("*.md"):
                    tmpl_txt = tmpl_file.read_text(encoding="utf-8")
                    if re.search(
                        r"(?:__TT__|\bTT\b)\s*\n\s*\n\s*__(?:Danh mục|Tên sản phẩm|Khoản mục)",
                        tmpl_txt,
                    ):
                        if "|" not in tmpl_txt:
                            errors.append(
                                f"Broken Table Error [{tmpl_file.name}]: Flattened/vertical table detected. Must be converted to 2D GFM Pipe Table."
                            )

            # Check 3: Redundant table links in Semantic MOC
            if "## 📑 HỆ THỐNG PHỤ LỤC" in content or "## 📑 DANH MỤC PHỤ LỤC" in content:
                moc_part = content.split("## 📑")[1] if "## 📑" in content else ""
                if re.search(
                    r"-\s*📊\s*\[bang_\d+\]\(\./tables/csv/bang_\d+\.csv\)",
                    moc_part,
                ):
                    warnings.append(
                        f"Redundant Table Warning [{doc_dir.name}]: MOC contains generic '[bang_XX]' links. Ensure meaningful titles or clean redundant table exports."
                    )

            # Check 4: Markdown list item lazy continuation / paragraph collapsing
            all_md_files = [primary_md] + (
                list(templates_dir.rglob("*.md")) if templates_dir.exists() else []
            )
            for md_path in all_md_files:
                txt = md_path.read_text(encoding="utf-8")
                lines = txt.splitlines()
                for i in range(len(lines) - 1):
                    curr_line = lines[i].strip()
                    next_line = lines[i + 1].strip()
                    if curr_line.startswith(("- ", "+ ", "* ")) and next_line:
                        if not next_line.startswith(("- ", "+ ", "* ", "#", "|", ">")):
                            if re.match(
                                r"^(?:\d+\.\d+|\d+\.\d+\.\d+|Điều\s+\d+|Khoản\s+\d+|Mục\s+[IVXLCDM0-9]+)\b",
                                next_line,
                            ):
                                errors.append(
                                    f"Markdown Formatting Error [{md_path.name}:L{i + 2}]: "
                                    f"Sub-clause '{next_line[:30]}' immediately follows a list item without a blank line, causing it to collapse into the bullet point."
                                )

    return (errors, warnings)
