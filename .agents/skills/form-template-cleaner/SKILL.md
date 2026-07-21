---
name: form-template-cleaner
description: Sub-skill làm sạch biểu mẫu và tự động khôi phục tiêu đề biểu mẫu bị lỗi placeholder (dấu chấm lửng) bằng AI Gateway.
role: sub_skill
master_skill: markdown-document-processing
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Sub-skill: Form Template Cleaner

Kỹ năng này xử lý các biểu mẫu (tờ trình, mẫu biên bản, báo cáo) bị lỗi nhận nhầm dòng placeholder chứa dấu chấm lửng/nét đứt làm tiêu đề.

## Lệnh CLI Tự động
Để tự động quét dọn và khôi phục tiêu đề biểu mẫu bằng AI:
```bash
python -m mdconverter.cli clean-form --file [đường_dẫn_tệp_markdown]
```

## SOP Xử lý bằng Prompt (AI-assisted Recovery)
Khi chạy CLI hoặc khi muốn viết script Python tùy chỉnh gọi AI Gateway để khôi phục tiêu đề:

1. **Nhận dạng lỗi:**
   * Phần frontmatter `title` hoặc tiêu đề chính `#` ở dòng đầu của tệp có các ký tự placeholder như `............`, `.......(1).......`, `___`.
2. **Thu thập dữ liệu ngữ cảnh:**
   * Trích xuất 20 dòng đầu tiên của tệp Markdown để làm thông tin đầu vào.
3. **Mẫu Prompt gọi AI Gateway (`ccba-ai`):**
   ```python
   from ccba_ai import ai
   
   prompt = f"""
   Phân tích 20 dòng đầu của biểu mẫu pháp luật Việt Nam sau đây và suy luận ra tiêu đề chính thức của biểu mẫu đó.
   Tiêu đề biểu mẫu thường là dòng chữ viết hoa nổi bật (ví dụ: THÔNG BÁO KHỞI CÔNG..., ĐƠN ĐỀ NGHỊ CẤP PHÉP..., BÁO CÁO KẾT QUẢ...).
   Bỏ qua các dòng placeholder chấm lửng như "........", "............(1)............", "Kính gửi: ...".
   Chỉ trả về duy nhất chuỗi tiêu đề chính thức, không thêm bất kỳ văn bản giải thích nào khác.
   Nội dung 20 dòng đầu:
   {context_lines}
   """
   extracted_title = ai.chat(prompt)
   ```
4. **Cập nhật:**
   * Đè tiêu đề chuẩn `extracted_title` vào trường `title` của frontmatter và vào dòng tiêu đề `#` của tệp.
