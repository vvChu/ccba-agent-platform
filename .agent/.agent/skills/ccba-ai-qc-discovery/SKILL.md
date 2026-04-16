---
name: ccba-ai-qc-discovery
description: Tự động quét hồ sơ PDF, nhận diện cấu trúc bản vẽ, tìm mục lục và xây dựng Ma trận Phối hợp (Coordination Matrix).
---

# CCBA AI QC Discovery Skill

## Vai trò
Skill này giúp Agent "tự hiểu" cấu trúc của một bộ hồ sơ thiết kế đồ sộ mà không cần sự can thiệp thủ công. Nó tự động tìm kiếm các trang mục lục (Index pages), trích xuất mã bản vẽ (SheetNo) và phân loại theo tầng (Level)/khu vực (Zone).

## Cách sử dụng
Kích hoạt khi cần lập bản đồ dữ liệu cho một dự án mới hoặc một thư mục bản vẽ chưa được phân loại.

### Các Trigger
- "Discovery hồ sơ"
- "Lập bản đồ dự án"
- "Tạo Project Backbone"
- "Xây dựng Coordination Matrix"

## Công cụ đi kèm
- `scripts/discovery_engine.py`: Chạy quy trình cào metadata từ PDF.

## Quy tắc
1. Luôn kiểm tra 10 trang đầu của PDF để tìm mục lục trước khi thực hiện quét toàn bộ.
2. Sử dụng `ocr-primary` trên AI Gateway nếu PDF là bản quét (scanned).
3. Kết quả đầu ra luôn phải là tệp Markdown hoặc CSV chuẩn hóa để các Skill khác (vd: Audit) có thể đọc được.
