---
proposal_id: "2026-08-23_universal_table_and_template_extractor"
type: "tool"
name: "universal-table-and-template-extractor"
status: "merged"
merged_commit: "cd1a2bd6"
merged_date: "2026-08-23"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-08-23"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp điển"
---

# Proposal: Universal Table and Direct Form Template Extractor for OKF v2.2

## 1. Tóm Tắt & Bối Cảnh Thực Tế (Context & Pain Points)
Trong quá trình chuẩn hóa các gói tri thức pháp lý tại Spoke `ccba-legal-knowledge` (điển hình như **Thông tư 73/2026/TT-BTC**, **Thông tư 79/2026/TT-BTC**, và **Thông tư 41/2026/TT-BXD**):
1. **Lỗi vỡ dọc bảng biểu phức tạp:** Thư viện `mammoth` mặc định không hỗ trợ trích xuất đầy đủ cấu trúc bảng 2D Markdown cho các bảng danh mục lớn (như Bảng phân loại 217 hàng của Phụ lục I Thông tư 41), khiến bảng bị dàn phẳng thành hàng trăm đoạn văn bản rời rạc.
2. **Thiếu cơ chế bóc tách Form Template trực tiếp:** Các văn bản của Bộ Tài chính không sử dụng tiêu đề `PHỤ LỤC ...` mà định danh trực tiếp `Mẫu số XX/...`. Bộ bóc tách cũ bỏ sót toàn bộ các biểu mẫu này khiến thư mục `templates/` bị rỗng.
3. **Ô nhiễm bảng do gán nhầm tên:** Bộ phân loại bảng cũ có logic hardcode tên `bang_danh_muc_cong_trinh_anh_huong_an_toan_cong_dong` cho mọi bảng có từ khóa "quy mô".

---

## 2. Giải Pháp Triển Khai Trên Hub (Implementation Details)

Đã nâng cấp module [`packages/ccba-legal-intel/src/ccba_legal/docx_converter.py`](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/src/ccba_legal/docx_converter.py):
1. **Khử hoàn toàn Hardcode Table Slug:** Thay thế logic định danh cứng bằng chuẩn `bang_{idx:02d}` an toàn và nhất quán.
2. **Bóc tách Biểu Mẫu Trực Tiếp (`direct_form_matches`):** Tự động phát hiện và trích xuất các biểu mẫu có định dạng `Mẫu số XX/...` (hoặc `Mẫu số 01(i)/DT-QLDA`, `Mẫu số 01.QĐ/QT-QLDA`...) khi văn bản không có tiêu đề `PHỤ LỤC`.
3. **Tái tạo chuẩn 2D GFM Pipe Tables:** Hỗ trợ render bảng 2D chuẩn GFM có bọc `<br>` cho ô đa dòng, lọc bỏ các dòng tiêu đề lặp lại từ Microsoft Word và dọn dẹp các cột rỗng ở cuối.

---

## 3. Kiểm Thử & Nghiệm Thu (Verification & QA)

- **Ruff Check & Format:** Vượt qua 100% ruff linting (`All checks passed!`).
- **Unit Tests:** Toàn bộ test suite của `ccba-legal-intel` pass 100%.
- **Spoke Production Parity:** Đã kiểm thử và nghiệm thu thực tế trên toàn bộ 26 gói văn bản tại `ccba-legal-knowledge`, vượt qua 24/24 regression tests và 100% PDF SHA-256 validation.
