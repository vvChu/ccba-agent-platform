# Lộ Trình Hiện Thực Hóa Phương Pháp Luận Lập Trình Agentic trên CCBA Platform

Tài liệu này vạch ra các bước kỹ thuật cụ thể để tích hợp cả 3 trụ cột của Phương pháp luận lập trình Agentic (Context, Harness, Nhận thức) vào nền tảng **ccba-agent-platform**.

---

## 1. Trụ Cột 1: Kỹ Nghệ Ngữ Cảnh (Context Engineering)

### 🚀 Cơ chế Giám sát Token & Cảnh báo D-Zone
* **Mục tiêu**: Giữ cho dung lượng phiên chat luôn dưới 40% (Smart Zone) để tránh hiện tượng Lost-in-the-Middle và ảo giác.
* **Hiện thực hóa**:
  - Viết một middleware/hook giám sát tổng số token trong phiên.
  - Khi token vượt quá 40% giới hạn của mô hình (ví dụ: > 80k token đối với cửa sổ 200k), in cảnh báo đỏ trên statusline: `[WARNING] Context entered D-Zone! Please run /session-retrospective to compact state.`
  - Cung cấp lệnh `/session-retrospective` để tự động tóm tắt toàn bộ tệp tin đã sửa, kết quả test và sơ đồ kiến trúc vào `.md/session_learnings.md` và `latest.md`, sau đó reset session.

---

## 2. Trụ Cột 2: Kỹ Nghệ Môi Trường (Harness Engineering)

### 🚀 Vòng Lặp Tự Vá Lỗi Sau Hành Động (Post-action Self-Healing Hook)
* **Mục tiêu**: Cưỡng chế chạy kiểm tra chất lượng và unit test bằng máy móc ngay sau khi Agent thay đổi mã nguồn.
* **Hiện thực hóa**:
  - Đăng ký hook `PostToolUse` cho các công cụ sửa đổi tệp tin (`replace_file_content`, `write_to_file`).
  - Mỗi khi Agent hoàn thành việc ghi file `.py`, hook sẽ tự động kích hoạt ngầm:
    ```bash
    ruff check --fix packages/
    pytest tests/
    ```
  - Nếu phát hiện lỗi lint hoặc test thất bại, hệ thống sẽ tự động bắt lấy stack trace và đẩy ngược vào context của Agent dưới dạng: `[System Hook Error] Linter/Test failed after your write. Traceback:... Please resolve this error before proceeding.`
  - Agent buộc phải sửa lỗi này thành công mới có thể gửi yêu cầu phê duyệt cho người dùng.

---

## 3. Trụ Cột 3: Quản Trị Nhận Thức (Cognitive Stewardship)

### 🚀 Quy trình Thiết kế Đặc tả Trước (Spec-First Development)
* **Mục tiêu**: Ngăn chặn bẫy vibe-coding (chấp nhận code mù quáng từ AI), kiểm soát Nợ Thấu Hiểu (Comprehension Debt).
* **Hiện thực hóa**:
  - Tạo template đặc tả bắt buộc `spec.md` tại thư mục `.md/specs/` cho mọi tính năng mới.
  - Trước khi code, Agent và lập trình viên phải thống nhất:
    1. Thiết kế API / dataflow.
    2. Các kịch bản biên (edge cases).
    3. Định nghĩa các ca kiểm thử (test cases) cụ thể.
  - Mã nguồn chỉ được triển khai sau khi `spec.md` được con người phê duyệt thủ công.

### 🚀 Nhật Ký Quyết Định Kiến Trúc Tự Động (ADR Generator)
* **Mục tiêu**: Tránh việc hệ thống trở thành "hộp đen" khi code phình to.
* **Hiện thực hóa**:
  - Tích hợp một tác tử phân tích Git diff định kỳ.
  - Khi phát hiện các thay đổi cấu trúc lớn (như thêm package mới, đổi database schema, sửa API Core), tự động tạo một file ADR (Architecture Decision Record) dưới dạng Markdown lưu tại `.md/knowledge/adr/`.
  - File ADR ghi nhận rõ: Bối cảnh, Đề xuất giải pháp, Lợi ích/Rủi ro đối chiếu (Trade-offs).

### 🚀 Rà Soát Mã Nguồn Định Kỳ (Automated Code Review Loop)
* **Mục tiêu**: Kiểm soát Nợ Nhận Thức (Cognitive Debt), cảnh báo khi mã nguồn phình to quá mức kiểm soát của con người.
* **Hiện thực hóa**:
  - Thiết lập tác tử kiểm tra định kỳ (chạy hàng tuần hoặc trước khi tạo PR).
  - Tác tử đánh giá độ phức tạp thuật toán (cyclomatic complexity), tỷ lệ bao phủ test (test coverage), và đưa ra báo cáo cảnh báo nếu phát hiện các module "rác" hoặc quá phức tạp khó bảo trì.
