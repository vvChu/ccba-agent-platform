---
description: Chuyển đổi tài liệu sang Markdown bằng mdconverter
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: Convert to Markdown

Khi user gọi lệnh `/convert-markdown [đường_dẫn_file_hoặc_thư_mục] [các_tùy_chọn]`, thực hiện các bước sau:

## Bước 1: Xác định tham số
1. Lấy `[đường_dẫn_file_hoặc_thư_mục]` do user cung cấp. Nếu không có, yêu cầu user cung cấp.
2. Kiểm tra xem user có truyền thêm tùy chọn nào không (ví dụ: cờ `--ocr` cho PDF scan mờ, engine `-t gemini` hoặc đệ quy `-r`). 

> **Lưu ý (Quan trọng về OCR)**: Khi gặp tài liệu PDF bản scan bị mờ, lóa sáng, cong vênh, hoặc có dấu mộc đỏ đè lên chữ, Agent **cần** chèn cờ `--ocr` để sử dụng model AI thị giác chuyên nghiệp (ocr-primary) nhằm tránh lỗi trích xuất.
> 
> **Lưu ý (Về bản vẽ)**: Đối với các bản vẽ kỹ thuật (A3+), sử dụng cờ `--extract-drawing` để kích hoạt chế độ bóc tách ghi chú và bảng thông số thay vì skipped.


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
