# Sổ Tay Điền Form Word & Bảo Toàn Bố Cục (Form Filling & Layout Guard)

> **Mục đích:** Hướng dẫn AI Agent và Lập trình viên điền dữ liệu vào các biểu mẫu hành chính, hợp đồng, hồ sơ thị thực (Visa) định dạng `.doc` (Word 97-2003) hoặc `.docx` mà không làm vỡ cấu trúc bố cục, xé hàng qua trang hoặc sai lệch số trang in.
> **Package:** `ccba-ooxml` (sub-module `form_filler`)

---

## 1. Khi Nào Cần Dùng `WordFormFiller`?

- Biểu mẫu gốc được cung cấp dưới dạng nhị phân cổ điển `.doc` hoặc `.docx` có khung bảng cố định.
- Cần điền các trường văn bản (`{{HO_VA_TEN}}`, `{{NGAY_SINH}}`...) giữ nguyên font chữ, kích cỡ và định dạng.
- Cần điền danh sách lặp (thân nhân, quá trình công tác, danh mục vật tư...) vào bảng có sẵn hàng mẫu (template row).
- Cần bảo đảm **không xé hàng bảng qua 2 trang** và **tự động cắt tỉa hàng trống thừa**.
- Cần xuất trực tiếp sang file `.doc`, `.docx` hoặc `.pdf`.

---

## 2. Mã Nguồn Mẫu (Quickstart)

```python
from ccba_ooxml import FormFillConfig, TableRule, WordFormFiller

# 1. Khởi tạo filler với template (hỗ trợ cả .doc và .docx)
config = FormFillConfig(
    engine="auto",                  # Tự động chọn Winword COM trên Windows, Soffice trên Linux
    keep_font_formatting=True,      # Giữ nguyên định dạng font/size gốc
    prevent_row_split=True,         # Chống xé hàng qua trang (AllowBreakAcrossPages = False)
    prune_empty_rows=True,          # Tự động xóa các hàng mẫu trống không có dữ liệu
    page_break_keywords=["PHẦN KẾT LUẬN", "XÁC NHẬN CỦA ĐƠN VỊ"],
)

with WordFormFiller("bieu_mau_thi_thuc.doc", config=config) as filler:
    # 2. Điền các trường văn bản trong đoạn văn hoặc ô bảng
    filler.apply_paragraphs({
        "{{HO_VA_TEN}}": "VŨ VĂN CHỦ",
        "{{NGAY_SINH}}": "15/08/1990",
        "{{SO_HO_CHIEU}}": "C12345678",
        "{{DIA_CHI_THUONG_TRU}}": "Hà Nội, Việt Nam",
    })

    # 3. Điền bảng danh sách động
    filler.apply_tables([
        TableRule(
            table_index=0,          # Bảng đầu tiên trong văn bản
            data_rows=[
                {"STT": "1", "Họ Tên": "Nguyễn Văn A", "Quan Hệ": "Bố", "Năm Sinh": "1960"},
                {"STT": "2", "Họ Tên": "Trần Thị B", "Quan Hệ": "Mẹ", "Năm Sinh": "1965"},
            ],
            delete_unused_template_rows=True,  # Xóa các hàng mẫu trống còn lại
            allow_break_across_pages=False,    # Chống xé hàng
        )
    ])

    # 4. Xuất kết quả
    outputs = filler.export(
        doc_out="ho_so_hoan_thanh.doc",
        pdf_out="ho_so_hoan_thanh.pdf",
    )
    print("Đã xuất hồ sơ:", outputs)
```

---

## 3. Các Quy Tắc Bảo Toàn Layout (Form Layout Guard)

| Quy Tắc | COM (Windows Word) | OpenXML (Linux/Docker) | Tác Dụng |
| :--- | :--- | :--- | :--- |
| **Anti-Row Split** | `Row.AllowBreakAcrossPages = False` | `<w:trPr><w:cantSplit/></w:trPr>` | Ngăn không cho hàng bảng bị cắt ngang bởi trang in |
| **Prune Empty Rows** | `Row.Delete()` | `tr.getparent().remove(tr)` | Xóa các dòng template thừa khi số lượng item ít hơn số dòng mẫu |
| **Enforced Page Break** | `Paragraph.Format.PageBreakBefore = True` | `p.paragraph_format.page_break_before = True` | Đẩy các mục quan trọng (chữ ký, kết luận) sang trang mới |

---

## 4. Kiến Trúc Dual-Engine

- **Windows Native (`winword`):**
  - Tương tác In-Place Single-Pass trực tiếp trên Word DOM qua `win32com.client`.
  - Mở và lưu file `.doc` gốc mà không cần chuyển đổi trung gian.
  - Tự động đóng tài liệu và tắt tiến trình `WINWORD.EXE` trong khối `finally` an toàn.
- **Linux/Docker Fallback (`soffice`):**
  - Tự động kích hoạt trên các môi trường máy chủ Linux hoặc container Docker.
  - Sử dụng LibreOffice headless chuyển đổi `.doc` $\rightarrow$ `.docx`, thao tác XML bằng `python-docx`, sau đó chuyển đổi sang định dạng đích.
