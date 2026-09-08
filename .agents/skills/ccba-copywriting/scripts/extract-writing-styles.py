#!/usr/bin/env python3
# mypy: ignore-errors
"""
CCBA Style & Template Extractor.
Sử dụng AI Gateway để:
1. Phân tích văn phong (tông giọng, cấu trúc câu, từ vựng).
2. Tự động nhận diện cấu trúc biểu mẫu và sinh tệp tin Markdown Template (chứa các placeholders)
   để phục vụ làm dữ liệu mẫu đầu vào cho kỹ năng copywriting (/ccba-copywriting).

Usage:
    python extract-writing-styles.py --list
    python extract-writing-styles.py --style <tên-file-hoặc-thư-mục>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Đảm bảo UTF-8 trên Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Neo đường dẫn
PLATFORM_ROOT = Path(__file__).resolve().parents[4]
STYLES_DIR = PLATFORM_ROOT / "assets" / "writing-styles"
TEMPLATES_DIR = PLATFORM_ROOT / ".agents" / "skills" / "copywriting" / "templates"

# Thử nạp AI Gateway của CCBA
try:
    from ccba_ai import ai
except ImportError:

    class MockAI:
        def chat(self, prompt, system=None):
            return json.dumps(
                {
                    "style_analysis": "### Phong cách viết chung\n- Tông giọng: Trang trọng hành chính.\n- Từ vựng: Kỹ thuật xây dựng.",
                    "template": "# BIỂU MẪU ĐỀ XUẤT THẦU\n- Dự án: {{project_name}}\n- Chủ đầu tư: {{client_name}}",
                }
            )

    ai = MockAI()


def get_style_files() -> dict[str, Any]:
    """Liệt kê các tệp văn phong mẫu hoặc thư mục trong assets/writing-styles/"""
    if not STYLES_DIR.exists():
        STYLES_DIR.mkdir(parents=True, exist_ok=True)
    if not TEMPLATES_DIR.exists():
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    items = []
    for f in STYLES_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in {".md", ".txt"}:
            items.append(
                {"name": f.stem, "path": str(f), "is_dir": False, "size": f.stat().st_size}
            )
        elif f.is_dir() and not f.name.startswith("."):
            txt_files = list(f.glob("**/*.txt")) + list(f.glob("**/*.md"))
            items.append(
                {"name": f.name, "path": str(f), "is_dir": True, "file_count": len(txt_files)}
            )

    return {"items": sorted(items, key=lambda x: x["name"]), "directory": str(STYLES_DIR)}


from mdconverter.style import redact_sensitive_info


def call_ai_extract_api(content_text: str, target_name: str) -> tuple[str, str, str, str]:
    """Gửi yêu cầu phân tích lên AI Gateway và trả về (Style Analysis, Template, Category, DocumentType)"""
    system_prompt = (
        "Bạn là kiến trúc sư tri thức và chuyên gia thương hiệu của CCBA.\n"
        "Nhiệm vụ của bạn là nghiên cứu tài liệu mẫu được cung cấp để thực hiện các việc sau:\n"
        "1. Phân tích phong cách viết đặc trưng (Tone, cấu trúc câu, từ vựng, định dạng).\n"
        "2. Tự động nhận diện cấu trúc của tài liệu hành chính/thương mại đó, chuyển đổi thành "
        "một tệp BIỂU MẪU mẫu (Markdown Template) sạch sẽ. Thay thế các thông tin biến động bằng "
        "các placeholders dạng double-braces (ví dụ: {{client_name}}, {{project_name}}, {{delivery_date}}).\n"
        "   Nếu tài liệu chứa bảng biểu, hãy giữ nguyên tiêu đề cột và đánh dấu dòng lặp bằng:\n"
        "   <!-- ROW_START -->\n"
        "   | {{stt}} | {{placeholder}} | ... |\n"
        "   <!-- ROW_END -->\n"
        "3. Phân loại tài liệu thành nhóm phù hợp.\n\n"
        "Hãy phản hồi bằng định dạng JSON sạch sau:\n"
        "{\n"
        '  "style_analysis": "Chuỗi markdown phân tích văn phong chi tiết",\n'
        '  "category": "administrative hoặc commercial hoặc technical",\n'
        '  "document_type": "decision hoặc dispatch hoặc contract hoặc bid_proposal hoặc report hoặc other",\n'
        '  "template": "Chuỗi markdown biểu mẫu chứa placeholders"\n'
        "}"
    )

    user_prompt = f"""
    Hãy phân tích tài liệu mẫu sau đây để trích xuất văn phong và dựng biểu mẫu thô:

    ```text
    {content_text}
    ```
    """

    try:
        reply = ai.chat(user_prompt, system=system_prompt)

        # Làm sạch JSON
        clean_reply = reply.strip()
        if clean_reply.startswith("```json"):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith("```"):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()

        data = json.loads(clean_reply)
        return (
            data.get("style_analysis", ""),
            data.get("template", ""),
            data.get("category", "administrative"),
            data.get("document_type", "other"),
        )
    except Exception as e:
        print(f"[Error] Lỗi gọi AI Gateway hoặc parse JSON: {e}")
        return (
            f"### Phân tích văn phong (Lỗi phân tích JSON)\n\nTài liệu gốc: {target_name}",
            f"# BIỂU MẪU MẪU: {target_name}\n\n[Nội dung thô chưa trích xuất được template do lỗi]",
            "administrative",
            "other",
        )


def process_extraction(target_path: Path, target_name: str):
    """Xử lý trích xuất cho một tệp hoặc một thư mục tài liệu"""
    if target_path.is_dir():
        print(f"[Extractor] Đang quét thư mục mẫu: {target_path}")
        combined_content = []
        for f in target_path.glob("**/*"):
            if f.is_file() and f.suffix.lower() in {".md", ".txt"}:
                try:
                    text = f.read_text(encoding="utf-8")
                    combined_content.append(f"--- NỘI DUNG FILE MẪU: {f.name} ---\n{text[:2000]}")
                except Exception as e:
                    print(f"[Warn] Không đọc được tệp {f.name}: {e}")
        if not combined_content:
            print("[Error] Không tìm thấy file văn bản hợp lệ trong thư mục.")
            return
        content_text = "\n\n".join(combined_content)[:12000]
    else:
        print(f"[Extractor] Đang đọc tệp mẫu: {target_path}")
        content_text = target_path.read_text(encoding="utf-8")[:10000]

    # Thực hiện che giấu dữ liệu nhạy cảm (Maskara) trước khi gửi đi
    redacted_content = redact_sensitive_info(content_text)

    # Gọi AI Gateway
    style_analysis, template_content, category, doc_type = call_ai_extract_api(
        redacted_content, target_name
    )

    # 1. Ghi tệp phân tích văn phong
    style_output = STYLES_DIR / f"{target_name}_style_extracted.md"
    style_output.write_text(style_analysis, encoding="utf-8")
    print(f"[Success] Đã lưu tệp phân tích văn phong tại: {style_output}")

    # 2. Ghi tệp biểu mẫu mẫu (Template)
    if template_content and len(template_content) > 50:
        # Làm sạch tên file template để tránh các ký tự đặc biệt
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", target_name).lower()
        template_output = TEMPLATES_DIR / f"{safe_name}_template.md"

        # Thêm frontmatter cho template có chứa category và document_type phân loại
        final_template = f"""---
name: {safe_name}_template
category: {category}
document_type: {doc_type}
description: Biểu mẫu mẫu tự động sinh từ tài liệu nguồn {target_name}
---

{template_content}
"""
        template_output.write_text(final_template, encoding="utf-8")
        print(f"[Success] Đã tự động dựng và lưu tệp Biểu Mẫu (Template) tại: {template_output}")
    else:
        print("[Warn] Không nhận diện được biểu mẫu hoặc nội dung quá ngắn để dựng template.")


def main():
    parser = argparse.ArgumentParser(description="CCBA Style & Template Extractor")
    parser.add_argument(
        "--list", action="store_true", help="Liệt kê danh sách văn phong hành chính có sẵn"
    )
    parser.add_argument("--style", type=str, help="Tên file/thư mục mẫu hoặc đường dẫn trực tiếp")

    args = parser.parse_args()

    if args.list or not args.style:
        styles = get_style_files()
        print("\n# Danh sách văn phong/thư mục mẫu CCBA có sẵn:")
        print(f"Thư mục gốc: {styles['directory']}\n")
        if not styles["items"]:
            print(
                "Chưa có tệp văn phong mẫu nào. Hãy thêm file .txt/.md hoặc thư mục vào assets/writing-styles/"
            )
        else:
            print("| Tên tài sản | Loại tài sản | Chi tiết |")
            print("|---|---|---|")
            for f in styles["items"]:
                if f["is_dir"]:
                    print(f"| {f['name']} | Thư mục mẫu | {f['file_count']} tệp văn bản |")
                else:
                    print(f"| {f['name']} | Tệp mẫu đơn lẻ | {f['size'] / 1024:.1f} KB |")
        sys.exit(0)

    if args.style:
        # 1. Tìm trong STYLES_DIR
        target_path = STYLES_DIR / args.style
        target_name = args.style

        # 2. Tìm kiếm với đuôi mở rộng
        if not target_path.exists():
            matching_files = list(STYLES_DIR.glob(f"{args.style}.*"))
            if matching_files:
                target_path = matching_files[0]
                target_name = target_path.stem

        # 3. Phân giải đường dẫn trực tiếp
        if not target_path.exists():
            target_path = Path(args.style)
            target_name = target_path.stem

        if not target_path.exists():
            print(
                f"Lỗi: Không tìm thấy tệp hoặc thư mục '{args.style}' cục bộ hoặc trong assets/writing-styles/."
            )
            sys.exit(1)

        process_extraction(target_path, target_name)


if __name__ == "__main__":
    main()
