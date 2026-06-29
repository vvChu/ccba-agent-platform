import os
import re
import subprocess
import tempfile
from pathlib import Path


class TableReconstructor:
    """Core utility to reconstruct broken tables in markdown files using docx alignment."""

    def __init__(self) -> None:
        pass

    def reconstruct_table(self, md_path: Path, docx_path: Path) -> bool:
        """
        Reconstruct the table in md_path using content from docx_path.

        Args:
            md_path: Path to the target markdown file (usually a split appendix).
            docx_path: Path to the original parent docx file.

        Returns:
            True if successful, False otherwise.
        """
        if not md_path.exists() or not docx_path.exists():
            return False

        # 1. Read existing frontmatter
        frontmatter = self._get_frontmatter(md_path)

        # 2. Convert docx to GFM temp file
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w", encoding="utf-8"
        ) as temp_file:
            temp_md_path = Path(temp_file.name)

        try:
            # Run pandoc
            cmd = [
                "pandoc",
                "-f",
                "docx",
                "-t",
                "gfm",
                "--wrap=none",
                "-o",
                str(temp_md_path),
                str(docx_path),
            ]
            subprocess.run(cmd, check=True)

            with open(temp_md_path, encoding="utf-8") as f:
                temp_content = f.read()
        except Exception as e:
            print(f"Error converting docx with pandoc: {e}")
            if temp_md_path.exists():
                os.remove(temp_md_path)
            return False

        # 3. Detect which appendix this is
        appendix_id = self._detect_appendix_id(md_path)
        if not appendix_id:
            print(f"Could not detect appendix ID from file name: {md_path.name}")
            os.remove(temp_md_path)
            return False

        # 4. Extract section from temp file
        extracted_body = self._extract_section(temp_content, appendix_id)
        os.remove(temp_md_path)

        if not extracted_body:
            print(f"Could not extract section {appendix_id} from converted docx.")
            return False

        # 5. Patch links (fix relative links like appendices/)
        extracted_body = extracted_body.replace("(appendices/", "(./appendices/")

        # 6. Write back to md_path
        new_content = frontmatter + extracted_body
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    def _get_frontmatter(self, md_path: Path) -> str:
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            return f"---\n{match.group(1)}\n---\n\n"
        return ""

    def _detect_appendix_id(self, md_path: Path) -> str | None:
        # Detect appendix pattern: phu_luc_01, phu_luc_ii, etc.
        name_lower = md_path.name.lower()
        match = re.search(r"phu_luc_(\d+)", name_lower)
        if match:
            num = int(match.group(1))
            # Convert numeric index to Roman numeral
            return f"PHỤ LỤC {self._int_to_roman(num)}"
        return None

    def _int_to_roman(self, num: int) -> str:
        val = [10, 9, 5, 4, 1]
        syb = ["X", "IX", "V", "IV", "I"]
        roman_num = ""
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syb[i]
                num -= val[i]
            i += 1
        return roman_num

    def _extract_section(self, content: str, title: str) -> str:
        lines = content.splitlines(keepends=True)
        start_idx = -1
        end_idx = len(lines)

        # Search for pattern in lines
        # In GFM output, titles are often bolded: **PHỤ LỤC IV** or **PHỤ LỤC IV:**
        # Or they can be heading style: # PHỤ LỤC IV
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if (
                f"**{title}**" in clean_line
                or f"**{title}:**" in clean_line
                or clean_line.startswith(f"# {title}")
                or clean_line.startswith(f"## {title}")
            ):
                start_idx = i
                break

        if start_idx == -1:
            # Fallback to plain substring
            for i, line in enumerate(lines):
                if title in line:
                    start_idx = i
                    break

        if start_idx == -1:
            return ""

        # Find next appendix start
        # Extract the roman numeral or number index from the title to predict the next one
        match = re.search(r"PH\u1ee4 L\u1ee4C\s+([I|V|X]+)", title)
        if match:
            roman = match.group(1)
            num = self._roman_to_int(roman)
            next_roman = self._int_to_roman(num + 1)
            next_title = f"PHỤ LỤC {next_roman}"

            for i in range(start_idx + 1, len(lines)):
                clean_line = lines[i].strip()
                if (
                    f"**{next_title}**" in clean_line
                    or f"**{next_title}:**" in clean_line
                    or clean_line.startswith(f"# {next_title}")
                    or clean_line.startswith(f"## {next_title}")
                ):
                    end_idx = i
                    break

        return "".join(lines[start_idx:end_idx])

    def _roman_to_int(self, roman: str) -> int:
        roman_map = {"I": 1, "V": 5, "X": 10}
        num = 0
        for i in range(len(roman)):
            if i > 0 and roman_map[roman[i]] > roman_map[roman[i - 1]]:
                num += roman_map[roman[i]] - 2 * roman_map[roman[i - 1]]
            else:
                num += roman_map[roman[i]]
        return num
