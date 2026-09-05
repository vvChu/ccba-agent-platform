import argparse
import json
import os


def clone_xml_text(xml_file, map_file):
    if not os.path.exists(xml_file):
        print(f"Lỗi: Không tìm thấy file {xml_file}")
        return
    if not os.path.exists(map_file):
        print(f"Lỗi: Không tìm thấy file {map_file}")
        return

    with open(map_file, encoding="utf-8") as f:
        mapping = json.load(f)

    with open(xml_file, encoding="utf-8") as f:
        content = f.read()

    # Replace purely text mappings. Since XML nodes might break texts,
    # the mapping should match the exact text chunks inside <w:t> tags.
    # A safer approach for AI is replacing the exact string values.
    # Note: If text is broken across multiple <w:t> tags due to style changes,
    # the agent should be careful. This simple replace targets raw XML text.
    changes_made = 0
    for key, value in mapping.items():
        if key in content:
            content = content.replace(key, value)
            changes_made += 1
            print(f"Đã thay thế: '{key}' -> '{value}'")

    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SUCCESS] Hoàn tất phục chế. Đã thay thế {changes_made} dải từ khóa.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Tiêm nội dung mới vào lõi XML bảo toàn định dạng")
    parser.add_argument("xml_file", help="Đường dẫn đến file document.xml")
    parser.add_argument("--map", required=True, help="Đường dẫn file translation map JSON")
    args = parser.parse_args()

    clone_xml_text(args.xml_file, args.map)
