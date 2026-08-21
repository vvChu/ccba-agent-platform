---
proposal_id: "2026-08-20_okf_gold_standard_processor_gate4"
type: "tool"
name: "okf-gold-standard-processor-gate4"
status: "merged"
merged_commit: "217d77c"
merged_date: "2026-08-21"
priority: "High"
proposed_by_project: "ccba-legal-knowledge"
proposed_date: "2026-08-20"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Kiểm định"
  - "Khối Pháp lý & Tiêu chuẩn"
---

# Đề xuất Tích hợp: OKF v2.2 Gold Standard Processor & Cổng Kiểm định Visual Parity Gate 4

## 1. Mô tả
Đề xuất nâng cấp package **`packages/ccba-legal-intel`** trên Hub Monorepo, bổ sung 2 module xử lý và kiểm định chất lượng tài liệu pháp luật/quy chuẩn xây dựng theo chuẩn **OKF v2.2 Native-First (Pure Normative Body & Atomic Templates - ADR 0021)**:
1. **`GoldStandardProcessor` (`ccba_legal.gold_standard`)**:
   - **Xử lý Chú thích Chân bảng (Footnotes) & Chỉ số phụ (Superscripts):** Bóc tách các chú thích bị kẹt trong ô bảng HTML/Markdown thành khối độc lập `_GHI CHÚ CHỈ SỐ PHỤ:_`, định dạng chỉ số neo `<sup>X)</sup>`.
   - **Chuẩn hóa Danh sách & Header Chú thích:** Tự động khử trùng lặp tiêu đề `_CHÚ THÍCH:_`, căn chỉnh thụt lề 2 khoảng trắng (`  - `) cho các điều kiện con trong chú thích, loại bỏ bullet thừa trước các điểm `a)`, `b)` ở thân bài.
   - **Sinh AST & QA Benchmark Toàn diện:** Trích xuất tự động cây AST clauses và các cặp QA benchmark đối soát có phân định thẩm quyền (`CQXD` vs `CONG_AN`).
2. **`VisualParityAuditor` & `audit_visual_parity` (`ccba_legal.visual_parity`)**:
   - Engine kiểm định chất lượng hiển thị Markdown (Cổng CI Gate 4), phát hiện và chặn đứng mọi lỗi dồn dòng gạch đầu dòng (`- - `), double bullets, trapped table footnotes, concatenated inline dashes, unbulleted classification codes.

## 2. Vấn đề giải quyết
- **Lỗi vỡ layout Markdown khi bóc tách từ TVPL/DOCX:** Các văn bản quy chuẩn (như QCVN 06:2022/BXD, QCVN 04:2021/BXD) có cấu trúc bảng biểu phức tạp, chú thích chân bảng bị dồn thành hàng của bảng hoặc các ý con bị thụt lề sai khiến Markdown renderer hiểu nhầm.
- **Thiếu cổng kiểm định giao diện trước khi xuất bản:** Trước đây chỉ có cổng kiểm tra schema và integrity, chưa có gate tự động kiểm tra visual parity và bố cục danh sách đa cấp.
- **Tái sử dụng thống nhất trên toàn Platform (Reuse-First):** Tránh việc mỗi Spoke tự viết script regex riêng lẻ gây phân mảnh chuẩn OKF.

## 3. Danh sách các tệp đề xuất bổ sung/thay đổi
```text
packages/ccba-legal-intel/
  ├── src/
  │    └── ccba_legal/
  │         ├── __init__.py           (Export GoldStandardProcessor, VisualParityAuditor)
  │         ├── gold_standard.py      (Bộ xử lý chuẩn hóa chú thích, danh sách, sinh AST/QA)
  │         └── visual_parity.py      (Bộ kiểm định Visual & Footnote Parity Gate 4)
  └── tests/
       ├── test_gold_standard.py      (Unit tests cho GoldStandardProcessor)
       └── test_visual_parity.py      (Unit tests cho VisualParityAuditor)
```

## 4. Kết quả Kiểm thử & Nghiệm thu
- **Ruff Linter & Formatter:** Passed 100% (0 errors, 0 warnings).
- **Pytest Suite:** 100% Passed (bao gồm 7 test cases mới cho `test_gold_standard.py` và `test_visual_parity.py`).
- **Thực chứng tại Spoke `ccba-legal-knowledge`:** Đã xử lý và vượt qua 4 Cổng CI Gates trên 98 tệp Markdown của QCVN 06:2022, QCVN 04:2021, Nghị định 207/2026/NĐ-CP, Nghị định 217/2026/NĐ-CP.
