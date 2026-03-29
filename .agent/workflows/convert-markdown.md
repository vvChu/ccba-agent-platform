---
description: Chuyển đổi tài liệu sang Markdown bằng mdconverter
---

# Workflow: Convert to Markdown

Khi user gọi lệnh `/convert-markdown [đường_dẫn_file_hoặc_thư_mục] [các_tùy_chọn]`, thực hiện các bước sau:

## Bước 1: Xác định tham số
1. Lấy `[đường_dẫn_file_hoặc_thư_mục]` do user cung cấp. Nếu không có, yêu cầu user cung cấp.
2. Kiểm tra xem user có truyền thêm tùy chọn nào không (ví dụ: engine `-t gemini` hoặc đệ quy `-r`). 

## Bước 2: Thực thi chuyển đổi
Thực thi lệnh Python để gọi module mdconverter:

// turbo
3. Chạy lệnh:

```bash
python -m mdconverter.cli convert "[đường_dẫn_file_hoặc_thư_mục]" [các_tùy_chọn]
```

*(Agent tự động điền các tham số tương ứng vào lệnh trên)*

## Bước 3: Thông báo kết quả
4. Kiểm tra đầu ra của lệnh.
5. Thông báo kết quả cho user:
   - Trạng thái thành công/thất bại.
   - Thư mục lưu kết quả.
   - Trích xuất ngắn một đoạn nội dung (nếu user yêu cầu kiểm tra).
