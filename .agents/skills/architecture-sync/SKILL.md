---
name: architecture-sync
description: Đồng bộ hóa toàn bộ tài liệu kiến trúc (AGENTS.md, GEMINI.md, README.md) sau khi refactor codebase.
disable-model-invocation: true
---

# Constitution Sync: Architecture Synchronizer

Đồng bộ hóa toàn bộ tài liệu kiến trúc và hướng dẫn vận hành của hệ thống sau khi refactor cấu trúc thư mục hoặc thay đổi thiết kế module.

## Quy trình thực hiện

### Bước 1: Khảo sát Codebase (Legwork)
- Quét toàn bộ cây thư mục bằng công cụ `list_dir` hoặc lệnh tìm kiếm để phát hiện **tất cả** các tệp tin cấu hình kiến trúc:
  - `AGENTS.md` (Hiến pháp rào chắn)
  - `GEMINI.md` / `COPILOT.md` (Model routing và context)
  - `README.md` (Tổng quan kiến trúc)
- Ghi nhận chi tiết các module mới, dependencies mới và sơ đồ thư mục thực tế.

### Bước 2: Đồng bộ hóa Tài liệu
Cập nhật nội dung của tất cả các tệp cấu hình tìm thấy ở Bước 1 để phản ánh chính xác 100% codebase mới:
1. **`AGENTS.md`**: Cập nhật sơ đồ cấu trúc thư mục và các quy tắc/schemas mới.
2. **`GEMINI.md` / `COPILOT.md`**: Cập nhật Model Routing và hướng dẫn nạp context.
3. **`README.md`**: Cập nhật sơ đồ Mermaid (nếu có) và hướng dẫn chạy các scripts/CLI mới.

### Bước 3: Kiểm định Gác cổng (Linter Gate)
- Chạy linter tài liệu tĩnh để đảm bảo các tệp tin hiến pháp vừa cập nhật không bị hỏng liên kết hay chứa ký hiệu ảo giác:
  ```bash
  python scripts/validate_docs.py .
  ```
- Nếu phát hiện lỗi, bắt buộc phải sửa đổi hoàn chỉnh trước khi lưu trữ.

### Bước 4: Lưu trữ Knowledge Item (KI)
- Tạo một artifact tóm tắt (ví dụ: `walkthrough.md` hoặc `architecture_summary.md`) ghi nhận các thay đổi kiến trúc chính để chuyển tiếp tri thức sang phiên làm việc sau.

## Tiêu chí hoàn thành (Completion Criteria)
- `[ ]` Tất cả các tệp tin hiến pháp tìm thấy được cập nhật khớp 100% cấu trúc codebase mới.
- `[ ]` Lệnh kiểm định `validate_docs.py` chạy qua và không phát sinh lỗi liên kết hỏng.
- `[ ]` Artifact tóm tắt kiến trúc được tạo thành công trong thư mục artifacts.
