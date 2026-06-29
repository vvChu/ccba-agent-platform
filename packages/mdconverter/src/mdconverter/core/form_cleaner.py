import re
from pathlib import Path


class FormCleaner:
    """Core utility to clean form template placeholders and recover actual form titles using AI Gateway."""

    def __init__(self) -> None:
        pass

    def clean_form(self, file_path: Path) -> str:
        """
        Cleans placeholders in a markdown form file and recovers its official title.

        Args:
            file_path: Path to the markdown file to clean.

        Returns:
            The recovered title string if successful.

        Raises:
            ImportError: If ccba-ai package is not available.
            ValueError: If the file does not exist, has no frontmatter, or title recovery fails.
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        body_start = 0
        # Skip frontmatter
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    body_start = i + 1
                    break

        has_placeholders = False
        context_lines = []
        # Take first 25 lines of body to inspect
        body_sample_lines = lines[body_start : body_start + 25]
        for line in body_sample_lines:
            clean = line.strip()
            if re.search(r"\.{4,}", clean) or re.search(r"_{4,}", clean) or "(1)" in clean:
                has_placeholders = True
            context_lines.append(line)

        if not has_placeholders:
            return ""  # Skip, no placeholders

        # Call AI Gateway
        try:
            from ccba_ai import ai
        except ImportError as e:
            raise ImportError(
                "'ccba-ai' package is not installed. AI-assisted recovery is unavailable."
            ) from e

        context_text = "\n".join(context_lines)
        prompt = f"""
Phân tích 20 dòng đầu của biểu mẫu pháp luật Việt Nam sau đây và suy luận ra tiêu đề chính thức của biểu mẫu đó.
Tiêu đề biểu mẫu thường là dòng chữ viết hoa nổi bật (ví dụ: THÔNG BÁO KHỞI CÔNG XÂY DỰNG..., ĐƠN ĐỀ NGHỊ CẤP PHÉP..., BÁO CÁO KẾT QUẢ...).
Bỏ qua các dòng placeholder chấm lửng như "........", "............(1)............", "Kính gửi: ...".
Chỉ trả về duy nhất chuỗi tiêu đề chính thức được viết hoa, không thêm bất kỳ từ giải thích nào khác.

Nội dung 20 dòng đầu:
{context_text}
"""

        # Query AI Gateway with gemini-3.1-flash-lite (best for metadata extraction)
        raw_reply = ai.chat(prompt, model="gemini-3.1-flash-lite").strip()

        # Clean response and extract only the uppercase Vietnamese title line
        lines_reply = [line.strip() for line in raw_reply.splitlines() if line.strip()]
        filtered_lines = []
        for line in lines_reply:
            if re.match(
                r"^(here's|thinking|process|note|sure|i've|analysis|based on|the title|official)",
                line.lower(),
            ):
                continue
            filtered_lines.append(line)

        # Merge consecutive uppercase or title-like lines
        merged_lines = []
        current_upper = []
        for line in filtered_lines:
            if (
                line.isupper()
                or "PHỤ LỤC" in line
                or any(kwd in line for kwd in ["BÁO CÁO", "TỜ TRÌNH", "ĐƠN ĐỀ NGHỊ", "PHỤ LỤC"])
            ):
                current_upper.append(line)
            else:
                if current_upper:
                    merged_lines.append(" ".join(current_upper))
                    current_upper = []
                merged_lines.append(line)
        if current_upper:
            merged_lines.append(" ".join(current_upper))

        if merged_lines:
            # Prefer the longest merged uppercase/title line
            upper_lines = [
                line
                for line in merged_lines
                if line.isupper()
                or "PHỤ LỤC" in line
                or any(kwd in line for kwd in ["BÁO CÁO", "TỜ TRÌNH", "ĐƠN ĐỀ NGHỊ"])
            ]
            if upper_lines:
                recovered_title = max(upper_lines, key=len)
            else:
                recovered_title = max(merged_lines, key=len)
        else:
            recovered_title = raw_reply

        # Clean markdown formatting like bold stars if returned by LLM
        recovered_title = recovered_title.replace("**", "").replace("#", "").strip()
        # Merge multi-line titles into a single line
        recovered_title = " ".join(recovered_title.split())

        if not recovered_title or len(recovered_title) < 5:
            raise ValueError("AI Gateway returned empty or invalid title.")

        # Update frontmatter title and the main heading in lines
        # 1. Update frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            new_title_line = f'title: "PHỤ LỤC - {recovered_title}"'

            appendix_match = re.search(r"phu_luc_(\d+)", file_path.name.lower())
            if appendix_match:
                from mdconverter.core.table_reconstructor import TableReconstructor

                num = int(appendix_match.group(1))
                roman = TableReconstructor()._int_to_roman(num)
                new_title_line = f'title: "PHỤ LỤC {roman} - {recovered_title}"'

            fm_content_new = re.sub(r'title:\s*".*?"', new_title_line, fm_content)
            fm_content_new = re.sub(r"title:\s*.*?\n", new_title_line + "\n", fm_content_new)

            # 2. Update body heading
            heading_idx = -1
            for idx in range(body_start, len(lines)):
                if lines[idx].strip():
                    heading_idx = idx
                    break

            if heading_idx != -1:
                appendix_match = re.search(r"phu_luc_(\d+)", file_path.name.lower())
                if appendix_match:
                    from mdconverter.core.table_reconstructor import TableReconstructor

                    num = int(appendix_match.group(1))
                    roman = TableReconstructor()._int_to_roman(num)
                    lines[heading_idx] = f"# PHỤ LỤC {roman}\n\n{recovered_title}"
                else:
                    lines[heading_idx] = f"# {recovered_title}"

            # Reconstruct file
            new_content = f"---\n{fm_content_new}\n---\n\n" + "\n".join(lines[body_start:])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return recovered_title
        else:
            raise ValueError("No frontmatter detected in the markdown file.")
