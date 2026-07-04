# Biên bản Tổng hợp Quyết định: Phỏng vấn Áp dụng Docs Manager Agent

Biên bản này tổng hợp các quyết định kỹ thuật và giải pháp kiến trúc đã được thảo luận và phê duyệt thông qua phiên làm việc **`/ccba-grilling`** đối với đề xuất áp dụng **Docs Manager Agent (ClaudeKit)** vào hệ thống **ccba-agent-platform**.

---

## 📋 Quyết sách Kỹ thuật đã Thống nhất

### 1. Cơ chế Thiết lập Tài liệu Baseline ở Lần chạy Đầu tiên
*   **Quyết định**: Kích hoạt quy trình **Baseline Scouting** toàn diện khi khởi tạo tài liệu kỹ thuật lần đầu cho một codebase chưa có tài liệu.
*   **Giải pháp**:
    - Chia nhỏ codebase thành các phân vùng/module logic (ví dụ: các packages độc lập).
    - Khởi chạy song song tối đa **3-5 subagents** (để tối ưu hóa API quota) để nghiên cứu sâu cấu trúc, API của từng phân vùng.
    - Tổng hợp và hợp nhất (merge) các báo cáo từ subagents thành tài liệu baseline hoàn chỉnh.

### 2. Thực thi "Reuse-First Gate" và Hệ thống Templates
*   **Quyết định**: Cưỡng chế Agent kế thừa các biểu mẫu (templates) tài liệu kỹ thuật có sẵn từ Hub thay vì tự ý sáng tạo.
*   **Giải pháp**:
    - Lưu trữ các file mẫu chuẩn tại thư mục Hub trung tâm: `.agents/templates/` (bao gồm `project_overview_pdr_template.md`, `system_architecture_template.md`...).
    - Quy trình `/ccba-docs init` bắt buộc Agent phải đọc các template này trước khi điền dữ liệu thực tế từ codebase.
    - Yêu cầu Agent tự động viết mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)` trong các tài liệu PDR của dự án con (Spoke).

### 3. Đảm bảo An toàn Liên kết khi Phân rã Tài liệu (Size Limit Gate)
*   **Quyết định**: Cưỡng chế giới hạn 800 dòng (LOC) cho mỗi tệp tài liệu và tự động sửa các liên kết tương đối bị ảnh hưởng khi chia nhỏ tệp.
*   **Giải pháp**:
    - Sử dụng sub-skill **`relative-link-patcher`** để tự động cập nhật liên kết trong tệp `index.md` và các tệp liên quan sau khi phân rã tệp tin lớn.
    - Chạy thử công cụ kiểm định **`validate_docs.py`** với tùy chọn quét nhanh các tệp thay đổi:
      ```bash
      python scripts/validate_docs.py . --changed
      ```
    - Nếu phát hiện lỗi liên kết hỏng (`Exit 1`), chặn cứng luồng, không ghi nhận commit/PR và bắt buộc Agent phải tự động khắc phục.

### 4. Phòng chống Rò rỉ Dữ liệu Nhạy cảm từ Repomix
*   **Quyết định**: Áp dụng các chốt bảo mật để bảo vệ thông tin mật khi Repomix đóng gói codebase.
*   **Giải pháp**:
    - Cấu hình bắt buộc tệp `.repomixignore` để loại bỏ tệp tin môi trường, keys, certificates.
    - Gọi kỹ năng **`maskara-privacy`** quét qua tệp tin đóng gói `repomix-output.xml` để tự động che giấu (redact) hoặc báo lỗi chặn tiến trình nếu phát hiện API Keys/Credentials.
    - Thực hiện xóa bỏ hoàn toàn tệp tin tạm `repomix-output.xml` trong thư mục `.md/scratch/` ngay sau khi kết thúc phiên hoạt động `/ccba-docs`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
