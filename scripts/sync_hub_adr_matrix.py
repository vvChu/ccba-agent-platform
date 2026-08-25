"""sync_hub_adr_matrix.py - Hub ADR Matrix Compiler & Living Traceability Engine."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows terminal
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")


def parse_adr_file(adr_path: Path) -> dict[str, Any]:
    """Extract metadata from an ADR markdown file."""
    content = adr_path.read_text(encoding="utf-8")

    # Extract ID and Title from H1
    h1_match = re.search(r"^#\s*ADR\s*0*([0-9]+)[:\s-]+(.*)$", content, re.MULTILINE | re.IGNORECASE)
    if h1_match:
        adr_num = int(h1_match.group(1))
        adr_title = h1_match.group(2).strip()
    else:
        fname_match = re.match(r"^0*([0-9]+)-(.*)\.md$", adr_path.name)
        if fname_match:
            adr_num = int(fname_match.group(1))
            adr_title = fname_match.group(2).replace("-", " ").title()
        else:
            adr_num = 0
            adr_title = adr_path.stem

    # Extract Status
    status = "ACCEPTED"
    status_match = re.search(r"##\s*1\.\s*Trạng Thái\s*\(Status\)\s*\n\s*\*\*([A-Z_]+)", content, re.IGNORECASE)
    if status_match:
        status = status_match.group(1).upper()
    elif "DEPRECATED" in content[:400]:
        status = "DEPRECATED"
    elif "SUPERSEDED" in content[:400]:
        status = "SUPERSEDED"

    return {
        "num": adr_num,
        "num_str": f"{adr_num:04d}",
        "title": adr_title,
        "filename": adr_path.name,
        "status": status,
        "path": adr_path,
        "content": content,
    }


def compile_hub_adr_readme(adr_list: list[dict[str, Any]], target_file: Path) -> str:
    """Generate docs/adr/README.md for Hub."""
    lines = [
        "# 🏛️ CCBA Agent Services Platform — Architectural Decision Records (ADRs)",
        "",
        "Tài liệu này lưu trữ toàn bộ các Quyết định Kiến trúc (ADRs) định hình nền tảng **CCBA Agent Services Platform (Hub)**, bao gồm Skills Framework, AI Gateway, Monorepo Packages, Governance, và Hub-Spoke Ecosystem.",
        "",
        "*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*",
        "",
        "---",
        "",
        f"## 📑 Danh Mục Quyết Định Kiến Trúc ({adr_list[0]['num_str']} — {adr_list[-1]['num_str']})",
        "",
        "| Mã ADR | Tiêu đề | Trạng thái |",
        "| :--- | :--- | :---: |",
    ]

    for adr in adr_list:
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        lines.append(f"| [ADR {adr['num_str']}]({adr['filename']}) | {adr['title']} | {status_icon} |")

    lines.append("")
    new_content = "\n".join(lines).strip() + "\n"
    target_file.write_text(new_content, encoding="utf-8")
    return new_content


def main() -> None:
    root_dir = Path.cwd()
    adr_dir = root_dir / "docs" / "adr"
    if not adr_dir.exists():
        print(f"[ERROR] Hub ADR directory not found at: {adr_dir}")
        sys.exit(1)

    adr_files = sorted(
        [f for f in adr_dir.glob("*.md") if f.name not in ("README.md", "TRACEABILITY_MATRIX.md")]
    )
    adr_list = [parse_adr_file(f) for f in adr_files]
    adr_list.sort(key=lambda x: x["num"])

    readme_path = adr_dir / "README.md"
    compile_hub_adr_readme(adr_list, readme_path)
    print(f"[sync_hub_adr_matrix] Successfully compiled: {readme_path.relative_to(root_dir)} ({len(adr_list)} ADRs)")


if __name__ == "__main__":
    main()
