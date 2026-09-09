# ccba-docs-validator — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Quy trình kiểm tra tính xác thực của tài liệu Markdown, ngăn ngừa ảo ảnh thông tin
> **Mô tả gốc:** Chạy kiểm định tài liệu Markdown chống ảo ảnh (hallucinations), broken links và cấu hình thiếu.

---

# Linter Gate: Docs Validator

Sử dụng kỹ năng này để chạy linter tài liệu tĩnh và tự động sửa các lỗi liên kết, ký hiệu ảo giác so với codebase thực tế.

## 1. Thực thi kiểm định
Để kiểm tra cực nhanh (chỉ quét các file có thay đổi qua Git), khuyên dùng:
```bash
python scripts/validate_docs.py . --changed
```
Hoặc quét toàn bộ workspace:
```bash
python scripts/validate_docs.py .
```

## 2. Quy trình xử lý lỗi (Legwork)
Khi báo cáo kiểm định trả về cảnh báo, thực hiện sửa đổi theo thứ tự ưu tiên:

- **Broken Link Error (Exit 1 - Chặn cứng)**:
  - *Hành động*: Định vị dòng bị lỗi liên kết tương đối, đối chiếu cấu trúc thư mục thực tế bằng `list_dir` và cập nhật lại đường dẫn chính xác.
- **Code Ref Warning (Cảnh báo mềm)**:
  - *Hành động*: Dùng `grep_search` quét codebase để tìm ký hiệu (class, function, variable) chính xác. Nếu ký hiệu đã bị xóa hoặc đổi tên, cập nhật tài liệu khớp 100% codebase thực tế. Tuyệt đối không giữ các ký hiệu không tồn tại.
- **Env Var Warning (Cảnh báo mềm)**:
  - *Hành động*: Nếu tài liệu nhắc tới biến môi trường chưa khai báo, bổ sung biến mẫu đó kèm mô tả ngắn gọn vào `.env.example` ở root dự án.

## 3. Tiêu chí hoàn thành (Completion Criteria)
- `[ ]` Chạy lại `validate_docs.py` và đảm bảo không còn lỗi `Exit 1` (Broken Link).
- `[ ]` Toàn bộ các cảnh báo `Code Ref` và `Env Var` mới phát sinh do thay đổi của phiên hiện tại được giải quyết triệt để.
