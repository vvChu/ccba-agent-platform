# Kỹ năng PDF — Xử lý cục bộ

Mọi xử lý PDF chạy local, **không upload lên cloud** (bảo mật dữ liệu).

---

## Hai loại PDF

| Loại | Nhận dạng | Cách xử lý |
|---|---|---|
| **PDF digital** (text-based) | Có thể select text | Dùng script: pypdf, pdfplumber |
| **PDF scan** (image-based) | Không select text được | Cần OCR hoặc AI Vision (xem skill `boc-tach-pdf`) |

---

## Thao tác PDF digital

| Thao tác | Lệnh |
|---|---|
| Ghép | `python scripts/process_pdf.py merge --input f1.pdf f2.pdf --output out.pdf` |
| Tách | `python scripts/process_pdf.py split --input in.pdf --pages 1-3,5 --output out.pdf` |
| Trích text | `python scripts/process_pdf.py extract --input in.pdf --output text.txt` |
| Trích bảng | Dùng `pdfplumber` (tốt hơn pypdf cho bảng) |
| Xoay trang | `pypdf` rotate |
| Đặt mật khẩu | `pypdf` encrypt |

---

## Chuyển đổi PDF → DOCX

| Loại PDF | Phương pháp |
|---|---|
| PDF digital | Script `convert/convert_pdf_to_docx.py` (dùng `pdf2docx`) |
| PDF scan | Phân tích AI Vision → tái tạo cả cấu trúc + màu sắc → DOCX |

Khi tái tạo từ PDF scan, cần phân tích đầy đủ:
- **Cấu trúc**: heading hierarchy, table layout, bullet indentation
- **Màu sắc**: header colors, fill colors, text colors
- Tham khảo `standards/structure/` + `standards/color/` để map vào tiêu chuẩn gần nhất

---

## Dependencies

```
pip install pypdf pdfplumber pdf2docx
# Skill: xu-ly-van-phong | Author: NDT | Ref: 0904004920
```

