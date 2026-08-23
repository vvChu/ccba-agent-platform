---
proposal_id: "2026-08-23_high_fidelity_markdown_renderer_and_gate8_guard"
type: "tool"
name: "high-fidelity-markdown-renderer-and-gate8-guard"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-08-23"
applies_to:
  - "Pháp lý"
  - "Thẩm tra thiết kế"
  - "QC Audit"
---

# Proposal: High-Fidelity Markdown Renderer & Gate 8 CI Structural Guard

## 1. Bối cảnh & Vấn đề Cốt lõi (Problem Statement)
Trong quá trình chuyển đổi các văn bản quy phạm pháp luật (VBPL) phức tạp (như Thông tư 34, 36, 37, 40/2026/TT-BXD) từ DOCX sang OKF v2.2 Markdown Bundle:
1. **Lỗi Nuốt Dòng Danh Sách (Markdown Lazy Continuation Collapse):** Khi một danh sách gạch đầu dòng (`- ...`) được theo sau bởi các tiểu mục luật (`2.2.1.`, `2.2.2.`, `a)`, `b)`) mà không có dòng trống (`\n\n`), trình phân giải Markdown tự động gom toàn bộ các đoạn văn bản sau thành nội dung của gạch đầu dòng đó, gây vỡ giao diện hiển thị.
2. **Thiếu Rào Chắn CI Gate Tự Động:** Chưa có module kiểm tra tự động phát hiện lỗi bảng biểu bị dàn phẳng, thiếu file templates khi thân luật có ban hành mẫu biểu, và lỗi nuốt dòng danh sách trước khi commit.

## 2. Giải pháp Kỹ thuật Đề xuất (Technical Solution)

### A. Nâng cấp Bộ Phân Đoạn & Render Markdown (`docx_converter.py`)
- **Tách Đoạn Bắt Buộc (`\n\n`):** Duy trì khoảng cách 2 dòng giữa các đoạn văn bản để đảm bảo ngữ cảnh danh sách được đóng đúng chuẩn CommonMark/GFM.
- **Định Dạng Tự Động Phân Cấp:** Tự động phát hiện và in đậm các tiểu mục `**2.2.1.**`, `**2.2.**`, `- a)`, `- b)` và đóng khung công thức toán học (`> **Công thức:** ...`).

### B. Module Kiểm Định Toàn Vẹn Cấu Trúc (`validator.py` - Gate 8 Guard)
- Bổ sung hàm `validate_template_and_table_integrity(spoke_root: Path)` với 4 chốt kiểm toán tự động:
  1. `Missing Templates Check`: Chặn văn bản nếu thân luật ban hành biểu mẫu nhưng `templates/` bị rỗng.
  2. `Broken Table Check`: Chặn các biểu mẫu có bảng bị dàn phẳng thành text mà không có cú pháp `| ... |`.
  3. `Redundant Table Check`: Cảnh báo liên kết bảng rác `[bang_XX]` trong Semantic MOC.
  4. `Lazy List Continuation Guard`: Chặn các tệp Markdown có tiểu mục nối tiếp trực tiếp gạch đầu dòng mà thiếu dòng trống `\n\n`.

## 3. Kế hoạch Kiểm Thử & Nghiệm Thu (Verification Plan)
- **Unit Tests:** Đã bổ sung bộ test `test_validator.py` kiểm tra 100% các kịch bản vi phạm và đạt PASS.
- **Regression:** Kiểm tra toàn bộ 26 gói tri thức tại Spoke `ccba-legal-knowledge` đều vượt qua với `0 Errors, 0 Warnings`.
