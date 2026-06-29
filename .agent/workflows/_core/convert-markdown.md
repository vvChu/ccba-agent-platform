---
description: Chuyển đổi tài liệu sang Markdown bằng mdconverter và tự động hậu xử lý (bảng biểu, biểu mẫu, liên kết)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: Convert to Markdown

Khi user gọi lệnh `/convert-markdown [đường_dẫn_file_hoặc_thư_mục] [các_tùy_chọn]`, thực hiện quy trình 3 bước khép kín sau:

## Bước 1: Chuyển đổi thô (Convert)
Thực thi lệnh Python để gọi module `mdconverter` chuyển đổi thô từ `.docx`/`.pdf` sang Markdown:
```bash
python -c "from mdconverter.cli import app; app()" convert "[đường_dẫn_file_hoặc_thư_mục]" [các_tùy_chọn]
```
*(Định dạng GFM mặc định của Pandoc sẽ tự động chuyển đổi các bảng phức tạp thành thẻ HTML `<table>` để bảo toàn cấu trúc).*

## Bước 2: Hậu xử lý sửa lỗi tự động (Post-process)
Sau khi chuyển đổi, Agent **bắt buộc** quét kiểm tra tệp tin `.md` đầu ra và tự động thực thi các subcommand để sửa lỗi:

1. **Khắc phục lỗi vỡ bảng biểu:**
   Nếu phát hiện tệp phụ lục chứa bảng biểu bị vỡ dọc (nhiều tab/dòng trống), chạy lệnh đối chiếu dựng lại bảng:
   ```bash
   python -c "from mdconverter.cli import app; app()" process-table --file "[tệp_md]" --docx "[tệp_docx_gốc]"
   ```
2. **Làm sạch placeholder & Phục hồi tiêu đề:**
   Nếu tệp là biểu mẫu (tờ trình, biên bản) có các dòng dấu chấm lửng placeholder ở đầu bị nhận nhầm làm tiêu đề, chạy lệnh:
   ```bash
   python -c "from mdconverter.cli import app; app()" clean-form --file "[tệp_md]"
   ```
3. **Chuẩn hóa liên kết tương đối:**
   Chạy lệnh sửa và chuẩn hóa các relative links của phụ lục về dạng `./appendices/`:
   ```bash
   python -c "from mdconverter.cli import app; app()" patch-links --file "[tệp_md_hoặc_thư_mục]"
   ```

## Bước 3: Đồng bộ Index
* Cập nhật và liên kết các file phụ lục mới/đổi tên vào file mục lục chính [index.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/legal_docs/luat_xay_dung_2025_so_135_2025_qh15/index.md) và phân nhóm theo đúng Nghị định cha để người dùng tiện tra cứu.
