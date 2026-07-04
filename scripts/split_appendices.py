import io
import re
import sys
from pathlib import Path

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def roman_to_decimal(r: str) -> int:
    """Convert Roman numeral string to decimal integer."""
    r = r.upper()
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50}
    val = 0
    for i in range(len(r)):
        if i > 0 and roman_map[r[i]] > roman_map[r[i - 1]]:
            val += roman_map[r[i]] - 2 * roman_map[r[i - 1]]
        else:
            val += roman_map[r[i]]
    return val


def main() -> None:
    base_dir = (
        Path(__file__).resolve().parents[1]
        / ".md"
        / "legal_docs"
        / "luat_xay_dung_2025_so_135_2025_qh15"
    )
    guiding_dir = base_dir / "guiding_docs"
    appendices_dir = guiding_dir / "appendices"
    appendices_dir.mkdir(parents=True, exist_ok=True)

    # Automatically scan all markdown files in the guiding_docs directory
    files = [f.name for f in guiding_dir.glob("*.md")]

    pattern = re.compile(
        r"^(?:#*|\**)\s*(PHỤ LỤC(?:\s+([IVXLCDM]+))?)\s*(?:\**)\s*$", re.IGNORECASE
    )

    all_appendices_links = []

    for fname in files:
        path = guiding_dir / fname
        if not path.exists():
            print(f"[Error] File not found: {path}")
            continue

        print(f"\nProcessing {fname}...")
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Step 1: Find matched lines
        matches = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                roman = m.group(2)
                matches.append((idx, m.group(1), roman))

        if not matches:
            print(f"No appendices found in {fname}")
            continue

        print(f"Found {len(matches)} appendices in {fname}.")

        # Step 2: Slice the files
        parent_slug = path.stem
        main_body_lines = lines[: matches[0][0]]

        # Clean trailing empty lines/white spaces from main body
        while main_body_lines and not main_body_lines[-1].strip():
            main_body_lines.pop()

        # Extract each appendix
        appendix_links = []
        for i, (idx, full_label, roman) in enumerate(matches):
            start_idx = idx
            end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(lines)

            app_lines = lines[start_idx:end_idx]

            # Remove header line from content so it is not duplicated below frontmatter
            app_lines.pop(0)

            # Find title
            title = ""
            for line in app_lines:
                cleaned = line.strip()
                # Skip blank lines and lines containing standard notes like "(Kèm theo...)"
                if cleaned and not cleaned.startswith("(") and not cleaned.endswith(")"):
                    title = cleaned.replace("#", "").strip()
                    break

            if not title:
                title = f"{full_label}"

            # Clean and standard decimal suffix
            if roman:
                dec_num = roman_to_decimal(roman)
                dec_str = f"{dec_num:02d}"
            else:
                dec_str = "01"
            app_filename = f"{parent_slug}-phu_luc_{dec_str}.md"
            app_path = appendices_dir / app_filename

            # Format frontmatter
            frontmatter = f"""---
type: Appendix
title: "{full_label} - {title}"
description: "Chi tiết {full_label} ban hành kèm theo {parent_slug.replace("_", " ").title()}"
parent_document: "../{fname}"
uniclass: "Fi_10_20"
---

# {full_label}

"""
            # Write appendix file
            app_content = frontmatter + "\n".join(app_lines).strip() + "\n"
            app_path.write_text(app_content, encoding="utf-8")
            print(f"  Created appendix file: guiding_docs/appendices/{app_filename}")

            # Register link
            link_entry = f"- [{full_label}: {title}](guiding_docs/appendices/{app_filename})"
            appendix_links.append(f"- [{full_label}: {title}](appendices/{app_filename})")
            all_appendices_links.append(link_entry)

        # Step 3: Re-write parent document with links at the bottom
        new_parent_content = "\n".join(main_body_lines).strip() + "\n\n"
        new_parent_content += "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM\n\n"
        new_parent_content += "\n".join(appendix_links) + "\n"

        path.write_text(new_parent_content, encoding="utf-8")
        print(f"Updated parent document with reference links: {fname}")

    # Step 4: Update index.md
    index_path = base_dir / "index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")

        # Append lists of appendices to index.md if they aren't already there
        if "### Phụ lục đính kèm" not in index_content:
            appendix_section = "\n### Phụ lục đính kèm (Decree Appendices)\n\n"
            appendix_section += "\n".join(all_appendices_links) + "\n"

            # Write at the very end
            index_path.write_text(index_content.strip() + "\n" + appendix_section, encoding="utf-8")
            print("Updated index.md with Decree Appendices list.")

    print("\nAppendix splitting completed successfully!")


if __name__ == "__main__":
    main()
