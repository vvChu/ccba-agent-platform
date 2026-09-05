# Form Cleaner Reference

Tài liệu này quy định quy trình và mẫu Prompt AI Gateway để khôi phục tiêu đề biểu mẫu bị lỗi placeholder (dấu chấm lửng/nét đứt).

---

## 1. Dấu hiệu Nhận Biết Lỗi

Phần frontmatter `title` hoặc tiêu đề chính `#` ở dòng đầu của tệp có các ký tự placeholder như `............`, `.......(1).......`, `___`.

---

## 2. Quy trình Xử lý Bằng AI Gateway (`ccba-ai`)

1. **Trích xuất Ngữ cảnh:** Đọc 20 dòng đầu tiên của tệp Markdown để làm thông tin đầu vào.
2. **Mẫu Prompt gọi AI:**
```python
from ccba_ai import ai

prompt = f"""
Phân tích 20 dòng đầu của biểu mẫu pháp luật Việt Nam sau đây và suy luận ra tiêu đề chính thức của biểu mẫu đó.
Tiêu đề biểu mẫu thường là dòng chữ viết hoa nổi bật (ví dụ: THÔNG BÁO KHỞI CÔNG, ĐƠN ĐỀ NGHỊ CẤP PHÉP, BÁO CÁO KẾT QUẢ).
Bỏ qua các dòng placeholder chấm lửng như "........", "............(1)............", "Kính gửi: ...".
Chỉ trả về duy nhất chuỗi tiêu đề chính thức, không thêm bất kỳ văn bản giải thích nào khác.
Nội dung 20 dòng đầu:
{context_lines}
"""
extracted_title = ai.chat(prompt)
```
3. **Cập nhật:** Đè tiêu đề chuẩn `extracted_title` vào trường `title` của frontmatter và vào dòng tiêu đề `#` của tệp.

---

## 3. Lệnh CLI Tự Động

```bash
python -m mdconverter.cli clean-form --file [đường_dẫn_tệp_markdown]
```
