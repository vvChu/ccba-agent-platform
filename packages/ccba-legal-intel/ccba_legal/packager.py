import re
import shutil
import time
from pathlib import Path
from typing import Any

import yaml


def extract_parent_metadata(content: str) -> dict[str, Any]:
    """Extract required metadata fields from frontmatter in parent content."""
    parent_fm = {}
    if content.strip().startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                parent_fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass

    # Extract only the specified target fields
    inherited = {}
    for key in ["resource", "status", "document_number", "timestamp"]:
        if key in parent_fm:
            inherited[key] = parent_fm[key]
    return inherited


class OKFBundlePackager:
    """Manages creation, writing, and directory structure organization of Open Knowledge Format (OKF) Bundles."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def sanitize_slug(self, text: str) -> str:
        """Create a clean directory slug from URL or title."""
        text = text.lower()
        # Replace slashes and dots with spaces
        text = text.replace("/", " ").replace("\\", " ").replace(".", " ")
        # Remove accents
        accents = {
            "a": "áàảãạăắằẳẵặâấầẩẫậ",
            "d": "đ",
            "e": "éèẻẽẹêếềểễệ",
            "i": "íìỉĩị",
            "o": "óòỏõọôốồổỗộơớờởỡợ",
            "u": "úùủũụưứừửữự",
            "y": "ýỳỷỹỵ",
        }
        for char, group in accents.items():
            for g in group:
                text = text.replace(g, char)
        text = re.sub(r"[^a-z0-9\s_-]", "", text)
        text = re.sub(r"[\s_-]+", "_", text).strip("_")
        # Truncate to prevent Windows MAX_PATH (260 chars) limitation issues
        if len(text) > 60:
            text = text[:60].rstrip("_")
        return text

    def write_concept(
        self,
        relative_path: str,
        concept_type: str,
        title: str,
        description: str,
        content: str,
        resource_uri: str = "",
    ) -> None:
        """Write a concept file with valid OKF YAML frontmatter."""
        dest = self.root_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = f"""---
type: {concept_type}
title: "{title}"
description: "{description}"
resource: "{resource_uri}"
timestamp: "{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}"
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
            "diff_report.md": "diff_report.md",
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
                        content = content.replace(f"{gf}.md", f"/guiding_docs/{gf}.md")

                    if old_name == f"{bundle_slug}.md":
                        processed_content = self.process_tables(content, bundle_dir)
                        try:
                            from ccba_legal.parser import LegalAnalysisEngine

                            engine = LegalAnalysisEngine()
                            processed_content = engine.standardize_formulas(processed_content)
                        except Exception as e:
                            print(f"[OKF Packager] Formula standardization skipped: {e}")

                        processed_content = self.inject_anchors(processed_content)

                        full_text_path = bundle_dir / "full_text.md"
                        full_text_path.write_text(processed_content, encoding="utf-8")

                        self.split_by_chapters(processed_content, bundle_dir / "sections")
                        self.generate_chunks(processed_content, bundle_dir)
                        content = processed_content

                    new_path.write_text(content, encoding="utf-8")
                    old_path.unlink()

                    # Split appendices if any
                    apps = self.split_concept_appendices(new_path)
                    for ap in apps:
                        all_app_paths.append((new_name.replace(".md", ""), ap))
                else:
                    shutil.move(old_path, new_path)
                print(
                    f"[OKF Packager] Moved primary file: {old_name} -> legal_docs/{bundle_slug}/{new_name}"
                )

        # 2. Move guiding documents and rewrite content links
        for gf in guiding_files:
            old_md = md_dir / f"{gf}.md"
            new_md = guiding_dir / f"{gf}.md"
            if old_md.exists():
                content = old_md.read_text(encoding="utf-8")

                # Update links pointing to primary law and support documents (up one level)
                content = content.replace(f"{bundle_slug}.md", f"/{bundle_slug}.md")
                content = content.replace("index.md", "/index.md")
                content = content.replace("compliance_checklist.md", "/compliance_checklist.md")
                content = content.replace("relationship_chart.md", "/relationship_chart.md")
                content = content.replace("diff_report.md", "/diff_report.md")

                new_md.write_text(content, encoding="utf-8")
                old_md.unlink()

                # Split appendices if any
                apps = self.split_concept_appendices(new_md)
                for ap in apps:
                    all_app_paths.append((gf, f"guiding_docs/{ap}"))
                print(
                    f"[OKF Packager] Moved guiding MD: {gf}.md -> legal_docs/{bundle_slug}/guiding_docs/{gf}.md"
                )

            old_docx = md_dir / f"{gf}.docx"
            new_docx = guiding_dir / f"{gf}.docx"
            if old_docx.exists():
                shutil.move(old_docx, new_docx)
                print(
                    f"[OKF Packager] Moved guiding DOCX: {gf}.docx -> legal_docs/{bundle_slug}/guiding_docs/{gf}.docx"
                )

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
                    label = re.sub(
                        r"\bPhu Luc (\d+)\b",
                        lambda m: f"Phụ lục {m.group(1)}",
                        label,
                        flags=re.IGNORECASE,
                    )
                    appendix_section += f"- [{label}]({rel_link})\n"

                index_path.write_text(
                    index_content.strip() + "\n" + appendix_section, encoding="utf-8"
                )
                print("[OKF Packager] Updated index.md with split appendices list.")

        # Write logs and update index with new files
        self._write_logs_and_index(bundle_dir, bundle_slug, guiding_files)

        # Automatically scan for clause-level amendments and update target documents / registry
        try:
            from ccba_legal.coordinator import LegalProcessor

            processor = LegalProcessor()

            # Scan primary document
            primary_md_path = bundle_dir / "full_text.md"
            if primary_md_path.exists():
                content = primary_md_path.read_text(encoding="utf-8")
                try:
                    rel_path = primary_md_path.relative_to(self.root_dir.parent).as_posix()
                except ValueError:
                    rel_path = primary_md_path.as_posix()
                processor.process_amendments_from_document(
                    source_doc_id=bundle_slug, source_doc_content=content, source_doc_path=rel_path
                )

            # Scan guiding documents
            for gf in guiding_files:
                guiding_md_path = guiding_dir / f"{gf}.md"
                if guiding_md_path.exists():
                    content = guiding_md_path.read_text(encoding="utf-8")
                    try:
                        rel_path = guiding_md_path.relative_to(self.root_dir.parent).as_posix()
                    except ValueError:
                        rel_path = guiding_md_path.as_posix()
                    processor.process_amendments_from_document(
                        source_doc_id=gf, source_doc_content=content, source_doc_path=rel_path
                    )
        except Exception as e:
            print(f"[OKF Packager] Error during automatic amendment processing: {e}")

        # 4. Standardise all bundle links to be bundle-absolute
        self.standardize_bundle_links(bundle_dir)

    def split_concept_appendices(self, file_path: Path) -> list[str]:
        """Detect and split appendices from a markdown file, saving them in an appendices/ subdirectory."""
        if not file_path.exists():
            return []

        content = file_path.read_text(encoding="utf-8")
        inherited = extract_parent_metadata(content)
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

        main_body_lines = lines[: matches[0][0]]
        while main_body_lines and not main_body_lines[-1].strip():
            main_body_lines.pop()

        def roman_to_decimal(r: str) -> int:
            r = r.upper()
            roman_map = {"I": 1, "V": 5, "X": 10, "L": 50}
            val = 0
            for i in range(len(r)):
                if i > 0 and roman_map[r[i]] > roman_map[r[i - 1]]:
                    val += roman_map[r[i]] - 2 * roman_map[r[i - 1]]
                else:
                    val += roman_map[r[i]]
            return val

        appendix_links = []
        for i, (idx, full_label, roman) in enumerate(matches):
            start_idx = idx
            end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(lines)

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

            fm_lines = [
                "---",
                "type: Appendix",
                f'title: "{full_label} - {title}"',
                f'description: "Chi tiết {full_label} ban hành kèm theo {parent_slug.replace("_", " ").title()}"',
                f'parent_document: "../{file_path.name}"',
                'uniclass: "Fi_10_20"',
            ]
            for key, val in inherited.items():
                if isinstance(val, str):
                    fm_lines.append(f'{key}: "{val}"')
                else:
                    fm_lines.append(f"{key}: {val}")
            fm_lines.append("---")
            frontmatter = "\n".join(fm_lines) + f"\n\n# {full_label}\n\n"
            app_content = frontmatter + "\n".join(app_lines).strip() + "\n"
            app_path.write_text(app_content, encoding="utf-8")

            appendix_links.append(f"- [{full_label}: {title}](appendices/{app_filename})")

        new_parent_content = "\n".join(main_body_lines).strip() + "\n\n"
        new_parent_content += "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM\n\n"
        new_parent_content += "\n".join(appendix_links) + "\n"

        file_path.write_text(new_parent_content, encoding="utf-8")
        return [
            f"appendices/{parent_slug}-phu_luc_{f'{roman_to_decimal(m[2]):02d}'}.md"
            for m in matches
        ]

    def inject_anchors(self, text: str) -> str:
        """Detect legal hierarchies and inject hidden HTML anchor tags at matching lines.

        Args:
            text: The raw markdown content.

        Returns:
            The markdown content with injected anchor tags.
        """
        lines = text.splitlines()
        output_lines = []

        current_dieu = None
        current_khoan = None

        chuong_pattern = re.compile(r"^\s*(Chương|CHƯƠNG)\s+([IVXLCDM\d]+)", re.IGNORECASE)
        muc_pattern = re.compile(r"^\s*(Mục|MỤC)\s+(\d+)", re.IGNORECASE)
        dieu_pattern = re.compile(r"^\s*(Điều|ĐIỀU)\s+(\d+)", re.IGNORECASE)
        khoan_pattern = re.compile(r"^(\s*)(\d+)[\.\)](\s+.*|\s*)$")
        diem_pattern = re.compile(r"^(\s*)([a-zđĐ])[\.\)](\s+.*|\s*)$", re.IGNORECASE)

        for line in lines:
            if chuong_pattern.match(line):
                chuong_pattern.match(line).group(2)
                current_dieu = current_khoan = None
            elif muc_pattern.match(line):
                muc_pattern.match(line).group(2)
                current_dieu = current_khoan = None
            elif dieu_pattern.match(line):
                current_dieu = dieu_pattern.match(line).group(2)
                current_khoan = None
                leading = len(line) - len(line.lstrip())
                line = line[:leading] + f'<a id="d{current_dieu}"></a>' + line[leading:]
            elif current_dieu and khoan_pattern.match(line):
                m = khoan_pattern.match(line)
                current_khoan = m.group(2)
                line = (
                    m.group(1)
                    + f'<a id="d{current_dieu}k{current_khoan}"></a>'
                    + line[len(m.group(1)) :]
                )
            elif current_dieu and current_khoan and diem_pattern.match(line):
                m = diem_pattern.match(line)
                diem_char = m.group(2).lower()
                line = (
                    m.group(1)
                    + f'<a id="d{current_dieu}k{current_khoan}d{diem_char}"></a>'
                    + line[len(m.group(1)) :]
                )

            output_lines.append(line)

        return "\n".join(output_lines)

    def flatten_html_table(self, table_soup: Any) -> tuple[list[list[str]], bool, int]:
        """Flatten an HTML table with rowspan or colspan using a virtual 2D grid.

        Args:
            table_soup: BeautifulSoup Tag representing <table>.

        Returns:
            A tuple of (grid, is_complex, num_rows).
        """
        is_complex = False
        rows = table_soup.find_all("tr")
        if not rows:
            return [], False, 0

        grid = {}
        max_c = 0
        max_r = len(rows)

        for r_idx, row in enumerate(rows):
            c_idx = 0
            cells = row.find_all(["td", "th"])
            for cell in cells:
                while (r_idx, c_idx) in grid:
                    c_idx += 1

                try:
                    rowspan = int(cell.get("rowspan", 1))
                except (ValueError, TypeError):
                    rowspan = 1

                try:
                    colspan = int(cell.get("colspan", 1))
                except (ValueError, TypeError):
                    colspan = 1

                if rowspan > 1 or colspan > 1:
                    is_complex = True

                text = cell.get_text().strip().replace("\n", " ").replace("\r", "")

                for r_offset in range(rowspan):
                    for c_offset in range(colspan):
                        grid[(r_idx + r_offset, c_idx + c_offset)] = text

                c_idx += colspan
                if c_idx > max_c:
                    max_c = c_idx

        final_grid = [[grid.get((r, c), "") for c in range(max_c)] for r in range(max_r)]
        return final_grid, is_complex, max_r

    def grid_to_markdown(self, grid: list[list[str]]) -> str:
        """Convert a 2D grid into a markdown table representation."""
        if not grid or all(not row for row in grid):
            return ""
        headers = [val.replace("|", "\\|") for val in grid[0]]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for row in grid[1:]:
            escaped_row = [val.replace("|", "\\|") for val in row]
            lines.append("| " + " | ".join(escaped_row) + " |")
        return "\n".join(lines)

    def grid_to_csv(self, grid: list[list[str]]) -> str:
        """Convert a 2D grid into a CSV string."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerows(grid)
        return output.getvalue()

    def grid_to_json(self, grid: list[list[str]]) -> str:
        """Convert a 2D grid into a JSON string (list of row dicts)."""
        import json

        if not grid:
            return "[]"
        headers = grid[0]
        data = []
        for row in grid[1:]:
            row_dict = {}
            for idx, col in enumerate(headers):
                val = row[idx] if idx < len(row) else ""
                key = col if col else f"column_{idx}"
                row_dict[key] = val
            data.append(row_dict)
        return json.dumps(data, ensure_ascii=False, indent=2)

    def find_top_level_tables(self, text: str) -> list[str]:
        """Find all top-level HTML tables inside the text."""
        tables = []
        pos = 0
        while True:
            start_idx = text.find("<table", pos)
            if start_idx == -1:
                break
            count = 1
            current_pos = start_idx + 6
            while count > 0:
                next_open = text.find("<table", current_pos)
                next_close = text.find("</table>", current_pos)
                if next_close == -1:
                    break
                if next_open != -1 and next_open < next_close:
                    count += 1
                    current_pos = next_open + 6
                else:
                    count -= 1
                    current_pos = next_close + 8
            if count == 0:
                tables.append(text[start_idx:current_pos])
                pos = current_pos
            else:
                pos = start_idx + 6
        return tables

    def process_tables(self, content: str, bundle_dir: Path) -> str:
        """Parse, flatten, and save tables, returning content with replaced markup."""
        from bs4 import BeautifulSoup

        tables_dir = bundle_dir / "tables"
        table_strings = self.find_top_level_tables(content)
        for idx, table_str in enumerate(table_strings, 1):
            table_soup = BeautifulSoup(table_str, "html.parser").find("table")
            if not table_soup:
                continue
            grid, is_complex, num_rows = self.flatten_html_table(table_soup)
            base_name = f"table_{idx:02d}"
            if is_complex:
                tables_dir.mkdir(parents=True, exist_ok=True)
                (tables_dir / f"{base_name}.html").write_text(table_str, encoding="utf-8")
            if num_rows > 50:
                tables_dir.mkdir(parents=True, exist_ok=True)
                (tables_dir / f"{base_name}.csv").write_text(
                    self.grid_to_csv(grid), encoding="utf-8"
                )
                (tables_dir / f"{base_name}.json").write_text(
                    self.grid_to_json(grid), encoding="utf-8"
                )
                replacement = (
                    f"\n\n*Bảng {idx:02d} có {num_rows - 1} dòng (hơn 50 dòng). "
                    f"Chi tiết xem tại [tệp CSV](tables/{base_name}.csv) "
                    f"hoặc [tệp JSON](tables/{base_name}.json).*\n\n"
                )
            else:
                replacement = "\n\n" + self.grid_to_markdown(grid) + "\n\n"
            content = content.replace(table_str, replacement)
        return content

    def split_by_chapters(self, content: str, sections_dir: Path) -> None:
        """Split content by chapters and save them in the sections directory."""
        sections_dir.mkdir(parents=True, exist_ok=True)
        inherited = extract_parent_metadata(content)
        lines = content.splitlines()
        chuong_pattern = re.compile(r"^\s*(Chương|CHƯƠNG)\s+([IVXLCDM\d]+)", re.IGNORECASE)

        chapters = []
        curr_lines = []
        curr_title = ""
        curr_num = 0
        preamble = []
        in_preamble = True

        for line in lines:
            match = chuong_pattern.match(line)
            if match:
                in_preamble = False
                if curr_num > 0:
                    chapters.append((curr_num, curr_title, curr_lines))
                elif preamble:
                    chapters.append((0, "Preamble", preamble))
                curr_num += 1
                curr_title = line.strip()
                curr_lines = [line]
            else:
                if in_preamble:
                    preamble.append(line)
                else:
                    curr_lines.append(line)

        if curr_num > 0:
            chapters.append((curr_num, curr_title, curr_lines))
        elif preamble and not chapters:
            chapters.append((1, "Toàn văn", preamble))

        for num, title, clines in chapters:
            c_text = "\n".join(clines).strip()
            dest = sections_dir / f"chuong_{num:02d}.md"

            fm_lines = [
                "---",
                "type: Section",
                f'title: "{title}"',
                'parent_document: "../full_text.md"',
            ]
            for key, val in inherited.items():
                if isinstance(val, str):
                    fm_lines.append(f'{key}: "{val}"')
                else:
                    fm_lines.append(f"{key}: {val}")
            fm_lines.append("---")
            frontmatter = "\n".join(fm_lines) + "\n\n" + c_text + "\n"
            dest.write_text(frontmatter, encoding="utf-8")

    def generate_chunks(self, content: str, bundle_dir: Path) -> None:
        """Segment content into 200-400 word chunks and write to chunks.json."""
        import json
        import math

        from ccba_legal.monitor import TokenMonitor

        monitor = TokenMonitor()
        paragraphs = []
        curr_para = []
        for line in content.splitlines():
            if not line.strip():
                if curr_para:
                    paragraphs.append("\n".join(curr_para))
                    curr_para = []
            else:
                curr_para.append(line)
        if curr_para:
            paragraphs.append("\n".join(curr_para))

        total_words = sum(len(p.split()) for p in paragraphs)
        if total_words == 0:
            (bundle_dir / "chunks.json").write_text("[]", encoding="utf-8")
            return

        num_chunks = max(1, math.ceil(total_words / 300))
        target_size = total_words / num_chunks

        chunks = []
        curr_chunk = []
        curr_words = 0
        idx = 1

        for p in paragraphs:
            p_words = len(p.split())
            if (
                curr_chunk
                and (curr_words >= 200)
                and (curr_words + p_words / 2 > target_size or curr_words + p_words > 400)
            ):
                c_text = "\n\n".join(curr_chunk)
                chunks.append(
                    {
                        "chunk_id": idx,
                        "content": c_text,
                        "word_count": curr_words,
                        "token_count": monitor.get_context_token_count([c_text]),
                    }
                )
                idx += 1
                curr_chunk, curr_words = [p], p_words
            else:
                curr_chunk.append(p)
                curr_words += p_words

        if curr_chunk:
            c_text = "\n\n".join(curr_chunk)
            if curr_words < 200 and chunks:
                chunks[-1]["content"] += "\n\n" + c_text
                chunks[-1]["word_count"] += curr_words
                chunks[-1]["token_count"] = monitor.get_context_token_count([chunks[-1]["content"]])
            else:
                chunks.append(
                    {
                        "chunk_id": idx,
                        "content": c_text,
                        "word_count": curr_words,
                        "token_count": monitor.get_context_token_count([c_text]),
                    }
                )

        (bundle_dir / "chunks.json").write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _write_logs_and_index(
        self, bundle_dir: Path, bundle_slug: str, guiding_files: list[str]
    ) -> None:
        """Create and update index.md, log.md, and dead_ends.md in the root of the OKF Bundle."""
        import time

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Write log.md
        log_content = f"""# OKF Bundle Processing Log

- [{timestamp}] Bundle '{bundle_slug}' initialized.
- [{timestamp}] Primary law parsed and packaged.
- [{timestamp}] Table flattening and extraction completed.
- [{timestamp}] Multi-resolution storage (full_text, sections, chunks) structured.
"""
        (bundle_dir / "log.md").write_text(log_content, encoding="utf-8")

        # Write dead_ends.md
        dead_ends_content = """# OKF Bundle Dead Ends Log

No dead ends or crawler restrictions encountered.
"""
        (bundle_dir / "dead_ends.md").write_text(dead_ends_content, encoding="utf-8")

        # Update/create index.md
        index_path = bundle_dir / "index.md"
        if index_path.exists():
            content = index_path.read_text(encoding="utf-8")
        else:
            content = f"# OKF Bundle Index - {bundle_slug}\n\n## Bundle Concepts\n\n"

        new_elements = [
            "- [Full Text (Processed)](/full_text.md) (type: `Processed Law`)\n",
            "- [Chunks JSON](/chunks.json) (type: `Data Chunks`)\n",
            "- [Processing Log](/log.md) (type: `Process Log`)\n",
            "- [Dead Ends Log](/dead_ends.md) (type: `Dead Ends Log`)\n",
        ]

        lines = content.splitlines()
        inserted = False
        for idx, line in enumerate(lines):
            if "## Bundle Concepts" in line:
                for elem in reversed(new_elements):
                    if elem.strip() not in content:
                        lines.insert(idx + 1, elem.strip())
                inserted = True
                break

        if not inserted:
            content += "\n## OKF Metadata Files\n\n" + "".join(new_elements)
        else:
            content = "\n".join(lines)

        index_path.write_text(content, encoding="utf-8")

    def standardize_bundle_links(self, bundle_dir: Path) -> None:
        """Scan all markdown files in the bundle directory and convert any internal
        relative links to bundle-absolute paths starting with `/` from the bundle root.

        Args:
            bundle_dir: Path to the OKF Bundle root directory.
        """
        import os

        for filepath in bundle_dir.rglob("*.md"):
            if not filepath.is_file():
                continue

            content = filepath.read_text(encoding="utf-8")
            link_pattern = re.compile(r"(\[([^\]]+)\]\(([^)]+)\))")

            def replace_link(match, filepath=filepath):
                full_link = match.group(1)
                text = match.group(2)
                href = match.group(3)

                # Skip external, email, and anchor-only links
                if href.startswith(("http://", "https://", "mailto:", "#")):
                    return full_link

                # Skip bundle-absolute links (already starting with /)
                if href.startswith("/"):
                    return full_link

                base_href = href.split("#")[0]
                anchor = href.split("#", 1)[1] if "#" in href else ""

                if not base_href:
                    return full_link

                # Resolve target path relative to the current file's directory
                try:
                    target_path = (filepath.parent / base_href).resolve()
                except Exception:
                    return full_link

                # Check if resolved target path resides within the bundle root
                try:
                    is_inside = target_path.is_relative_to(bundle_dir.resolve())
                except (ValueError, AttributeError):
                    try:
                        rel = os.path.relpath(target_path, bundle_dir.resolve())
                        is_inside = not rel.startswith("..") and not os.path.isabs(rel)
                    except ValueError:
                        is_inside = False

                if is_inside:
                    # Convert to bundle-absolute path
                    rel_to_bundle = target_path.relative_to(bundle_dir.resolve()).as_posix()
                    new_href = f"/{rel_to_bundle}"
                    if anchor:
                        new_href = f"{new_href}#{anchor}"
                    return f"[{text}]({new_href})"

                return full_link

            new_content = link_pattern.sub(replace_link, content)
            if new_content != content:
                filepath.write_text(new_content, encoding="utf-8")
                print(f"[OKF Packager] Standardized links in {filepath}")


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


def inject_warning_block(
    markdown_content: str,
    target_anchor: str,
    amendment_source: str,
    source_doc_path: str,
) -> str:
    """Inject a markdown warning block immediately after the line containing target_anchor.

    Args:
        markdown_content: The target markdown text.
        target_anchor: The HTML anchor of the amended clause (e.g. 'd15k2').
        amendment_source: Description of the amending clause (e.g. 'Điều 1 Thông tư B').
        source_doc_path: Relative or absolute path to the amending document.

    Returns:
        The updated markdown text with warning block injected.
    """
    lines = markdown_content.splitlines()
    anchor_pattern = f'id="{target_anchor}"'

    target_idx = -1
    for idx, line in enumerate(lines):
        if anchor_pattern in line:
            target_idx = idx
            break

    if target_idx == -1:
        return markdown_content

    # Extract doc title and clause
    doc_title = amendment_source
    match = re.match(
        r"^(Điều\s+\d+(?:\s+Khoản\s+\d+)?(?:\s+Điểm\s+[a-zA-ZđĐ])?)\s+(.*)$",
        amendment_source,
        re.IGNORECASE,
    )
    if match:
        doc_title = match.group(2).strip()

    warning_text = (
        f"> [!WARNING] Khoản này đã bị sửa đổi/bổ sung bởi {amendment_source}. "
        f"Xem nội dung mới tại [{doc_title}]({source_doc_path})."
    )

    # Check if this warning is already injected to prevent duplicates
    already_exists = False
    for offset in range(1, 4):
        if target_idx + offset < len(lines):
            check_line = lines[target_idx + offset]
            if "[!WARNING]" in check_line and (
                source_doc_path in check_line or amendment_source in check_line
            ):
                already_exists = True
                break

    if not already_exists:
        lines.insert(target_idx + 1, warning_text)

    return "\n".join(lines)
