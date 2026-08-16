#!/usr/bin/env python3
"""demo_okf_v2_packaging.py - Demonstrates Packaging a Vietnamese Legal Decree into OKF Bundle v2.0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure utf-8 stdout on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add package root to sys.path
package_root = Path(__file__).resolve().parent.parent.parent / "packages" / "ccba-legal-intel" / "src"
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from ccba_legal.packager import OKFBundlePackager


def run_okf_packaging_demo() -> Path:
    """Packages Decree 105/2025/ND-CP into an ADR-0038 compliant OKF Bundle v2.0."""
    print("=" * 75)
    print("🏛️ THÍ NGHIỆM 4: ĐÓNG GÓI MẪU 1 VĂN BẢN THÀNH BUNDLE OKF v2.0 (ADR 0038)")
    print("=" * 75)

    root_output = Path("d:/GitHubProjects/ccba-agent-platform/.md/legal_docs")
    root_output.mkdir(parents=True, exist_ok=True)

    packager = OKFBundlePackager(root_output)

    doc_id = "nghi_dinh_105_2025_nd_cp"
    title = "Nghị định 105/2025/NĐ-CP: Quy định chi tiết thi hành một số điều của Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ"
    
    # 1. Raw Markdown content (Clean 100%, without YAML frontmatter)
    markdown_content = """# NGHỊ ĐỊNH 105/2025/NĐ-CP: QUY ĐỊNH CHI TIẾT THI HÀNH LUẬT PCCC & CNCH

## Chương I: QUY ĐỊNH CHUNG

### Điều 1. Phạm vi điều chỉnh
Nghị định này quy định chi tiết một số điều của Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ về điều kiện an toàn phòng cháy và chữa cháy, thẩm định thiết kế, nghiệm thu và kiểm tra an toàn PCCC đối với nhà và công trình xây dựng.

### Điều 2. Đối tượng áp dụng
Nghị định này áp dụng đối với cơ quan, tổ chức, hộ gia đình và cá nhân hoạt động trên lãnh thổ nước Cộng hòa xã hội chủ nghĩa Việt Nam.

## Chương II: THẨM ĐỊNH THIẾT KẾ VÀ NGHIỆM THU PCCC

### Điều 9. Phân định thẩm quyền thẩm định thiết kế PCCC
1. Cơ quan chuyên môn về xây dựng chủ trì thẩm định, thẩm tra thiết kế PCCC đối với phần Kiến trúc, giải pháp ngăn cháy, chống khói và khoảng cách an toàn PCCC trong quy trình thẩm định Báo cáo nghiên cứu khả thi.
2. Cơ quan Công an (PC07) thực hiện thẩm định thiết kế đối với hệ thống thiết bị phòng cháy chữa cháy cơ điện (báo cháy tự động, chữa cháy tự động, cấp nước chữa cháy ngoài nhà).

### Điều 14. Nghiệm thu và bàn giao công trình PCCC
1. Chủ đầu tư có trách nhiệm tổ chức nghiệm thu từng phần và nghiệm thu hoàn thành toàn bộ hệ thống PCCC trước khi đưa công trình vào khai thác sử dụng.
2. Văn bản chấp thuận kết quả nghiệm thu của cơ quan có thẩm quyền là căn cứ để đưa công trình vào sử dụng.
"""

    metadata = {
        "doc_id": doc_id,
        "doc_number": "105/2025/NĐ-CP",
        "title": title,
        "type": "vbpl",
        "category": "Nghị định",
        "issuer": "Chính phủ",
        "issued_date": "2025-05-15",
        "effective_date": "2025-07-01",
        "status": "effective",
        "source_url": "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Nghi-dinh-105-2025-ND-CP-thi-hanh-Luat-Phong-chay-chua-chay-va-cuu-nan-cuu-ho.aspx",
        "sha256": "4a7b9c1d8e2f3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
    }

    # 2. Package into OKF v2.0 Bundle
    print("\n⚡ 1. KÍCH HOẠT OKF BUNDLE PACKAGER (Tạo thư mục & phân tách SSOT)")
    bundle_path = packager.package_bundle(doc_id=doc_id, content=markdown_content, metadata=metadata)
    print(f"👉 Thư mục Bundle được tạo: {bundle_path}")

    # 3. Tạo tệp clauses.json (Flat AST index with hierarchical coordinates)
    clauses_data = [
        {
            "clause_id": "chuong-1",
            "anchor": "chuong-1",
            "node_type": "chapter",
            "parent_id": None,
            "title": "Chương I: QUY ĐỊNH CHUNG",
            "line_start": 3,
            "line_end": 10,
        },
        {
            "clause_id": "dieu-1",
            "anchor": "dieu-1",
            "node_type": "article",
            "parent_id": "chuong-1",
            "title": "Điều 1. Phạm vi điều chỉnh",
            "line_start": 5,
            "line_end": 7,
        },
        {
            "clause_id": "dieu-2",
            "anchor": "dieu-2",
            "node_type": "article",
            "parent_id": "chuong-1",
            "title": "Điều 2. Đối tượng áp dụng",
            "line_start": 8,
            "line_end": 10,
        },
        {
            "clause_id": "chuong-2",
            "anchor": "chuong-2",
            "node_type": "chapter",
            "parent_id": None,
            "title": "Chương II: THẨM ĐỊNH THIẾT KẾ VÀ NGHIỆM THU PCCC",
            "line_start": 11,
            "line_end": 22,
        },
        {
            "clause_id": "dieu-9",
            "anchor": "dieu-9",
            "node_type": "article",
            "parent_id": "chuong-2",
            "title": "Điều 9. Phân định thẩm quyền thẩm định thiết kế PCCC",
            "line_start": 13,
            "line_end": 17,
        },
        {
            "clause_id": "dieu-14",
            "anchor": "dieu-14",
            "node_type": "article",
            "parent_id": "chuong-2",
            "title": "Điều 14. Nghiệm thu và bàn giao công trình PCCC",
            "line_start": 18,
            "line_end": 22,
        },
    ]

    clauses_path = bundle_path / "clauses.json"
    clauses_path.write_text(json.dumps(clauses_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Đã tạo {clauses_path.name} (6 mục AST phẳng kèm phân cấp)")

    # 4. Tạo tệp qa_benchmark.json (5 trường Ground-Truth phục vụ RAG Grounding Gate)
    qa_benchmark_data = [
        {
            "question": "Cơ quan chuyên môn về xây dựng thẩm định những nội dung nào về PCCC theo Nghị định 105/2025/NĐ-CP?",
            "answer": "Thẩm định phần Kiến trúc, giải pháp ngăn cháy, chống khói và khoảng cách an toàn PCCC.",
            "anchor": "dieu-9-khoan-1",
            "citation": "Khoản 1 Điều 9 Nghị định 105/2025/NĐ-CP",
            "ground_truth_context": "1. Cơ quan chuyên môn về xây dựng chủ trì thẩm định, thẩm tra thiết kế PCCC đối với phần Kiến trúc, giải pháp ngăn cháy, chống khói và khoảng cách an toàn PCCC...",
        },
        {
            "question": "Cơ quan Công an (PC07) thẩm duyệt nội dung PCCC nào?",
            "answer": "Thực hiện thẩm định thiết kế đối với hệ thống thiết bị PCCC cơ điện (báo cháy tự động, chữa cháy tự động, cấp nước chữa cháy ngoài nhà).",
            "anchor": "dieu-9-khoan-2",
            "citation": "Khoản 2 Điều 9 Nghị định 105/2025/NĐ-CP",
            "ground_truth_context": "2. Cơ quan Công an (PC07) thực hiện thẩm định thiết kế đối với hệ thống thiết bị phòng cháy chữa cháy cơ điện...",
        },
    ]

    qa_path = bundle_path / "qa_benchmark.json"
    qa_path.write_text(json.dumps(qa_benchmark_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Đã tạo {qa_path.name} (2 câu hỏi đối chuẩn Ground-Truth 5 trường)")

    # 5. Tạo cấu trúc bảng tables/
    tables_dir = bundle_path / "tables"
    tables_json = tables_dir / "json"
    tables_csv = tables_dir / "csv"
    tables_json.mkdir(parents=True, exist_ok=True)
    tables_csv.mkdir(parents=True, exist_ok=True)

    table_sample = [
        {"STT": 1, "Bộ môn": "Kiến trúc & Ngăn cháy", "Thẩm quyền thẩm định": "Cơ quan chuyên môn về xây dựng"},
        {"STT": 2, "Bộ môn": "Hệ thống PCCC cơ điện (Báo cháy, Chữa cháy)", "Thẩm quyền thẩm định": "Cơ quan Công an (PC07)"},
    ]
    (tables_json / "bang_phan_dinh_tham_quyen.json").write_text(
        json.dumps(table_sample, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (tables_csv / "bang_phan_dinh_tham_quyen.csv").write_text(
        "STT,Bộ môn,Thẩm quyền thẩm định\n1,Kiến trúc & Ngăn cháy,Cơ quan chuyên môn về xây dựng\n2,Hệ thống PCCC cơ điện,Cơ quan Công an (PC07)\n",
        encoding="utf-8-sig",
    )
    print(f"✅ Đã tạo thư mục tables/ (json/ và csv/ UTF-8 with BOM)")

    # 6. Kiểm tra cấu trúc thư mục Bundle
    print("\n📂 2. CẤU TRÚC GÓI TRI THỨC OKF BUNDLE v2.0 HOÀN CHỈNH:")
    for item in sorted(bundle_path.rglob("*")):
        rel_path = item.relative_to(bundle_path)
        if item.is_file():
            size_kb = item.stat().st_size / 1024
            print(f"  ├── {str(rel_path):<40} ({size_kb:.2f} KB)")
        else:
            print(f"  📁 {str(rel_path)}/")

    print("\n✅ THÍ NGHIỆM 4: ĐÓNG GÓI BUNDLE OKF v2.0 HOÀN TẤT THÀNH CÔNG!")
    print("=" * 75)
    return bundle_path


if __name__ == "__main__":
    run_okf_packaging_demo()
