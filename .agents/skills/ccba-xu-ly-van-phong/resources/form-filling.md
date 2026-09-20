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

### 2.1. Tự Động Nhận Diện Nhãn & Điền Form Toàn Diện (`auto_map_fields`)

Phương thức `auto_map_fields(data)` tự động quét toàn bộ văn bản và điền 4 dạng biểu mẫu hành chính phổ biến:
1. **Free-text / Inline Paragraphs:** Tự động tìm nhãn kèm dấu chấm/gạch dưới (ví dụ `Họ và tên: ..........`) hoặc placeholder `{{key}}`, bảo toàn 100% font in đậm/kích thước gốc.
2. **Trường Dấu Kiểm (Checkboxes):** Tự động nhận diện `Nam [ ]   Nữ [ ]` hoặc `( ) Độc thân` và đánh dấu `[X]` tương ứng dữ liệu.
3. **Property Sheet Tables:** Bảng 2 cột hoặc 4 cột Key-Value, tự động phát hiện ô chứa nhãn và điền giá trị vào ô kế tiếp, tương thích với ô bị gộp (Merged Cells).
4. **Dynamic Data Tables:** Tự động đối sánh các trường danh sách (`list[dict]`) với tiêu đề bảng để sinh hàng động.

```python
import os
from pathlib import Path
import yaml
from ccba_ooxml import FormFillConfig, WordFormFiller, TemplateProtectionError

# Cascading Vault Resolver: Nạp dữ liệu cá nhân theo thứ tự ưu tiên
def load_personal_profile() -> dict:
    candidates = [
        Path("./.md/knowledge/personal_profile.yaml"),
        Path(os.path.expanduser("~/.ccba/personal_profile.yaml")),
        Path(os.environ.get("CCBA_PERSONAL_VAULT", "")),
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("Không tìm thấy tệp personal_profile.yaml. Vui lòng sao chép từ template mẫu.")

data = load_personal_profile()

config = FormFillConfig(
    engine="auto",
    keep_font_formatting=True,
    prevent_row_split=True,
    prune_empty_rows=True,
    read_only_template=True, # Immutable Template Guard bảo vệ template gốc
)

with WordFormFiller("mau_to_khai_thi_thuc.docx", config=config) as filler:
    filler.auto_map_fields(data).export(
        doc_out="to_khai_hoan_thanh.docx",
        pdf_out="to_khai_hoan_thanh.pdf",
    )
```

### 2.2. Điền Thủ Công (Manual Mapping)

```python
from ccba_ooxml import FormFillConfig, TableRule, WordFormFiller

config = FormFillConfig(
    engine="auto",
    keep_font_formatting=True,
    prevent_row_split=True,
    prune_empty_rows=True,
    page_break_keywords=["PHẦN KẾT LUẬN", "XÁC NHẬN CỦA ĐƠN VỊ"],
)

with WordFormFiller("bieu_mau_thi_thuc.doc", config=config) as filler:
    # 1. Điền các trường văn bản trong đoạn văn hoặc ô bảng
    filler.apply_paragraphs({
        "{{HO_VA_TEN}}": "VŨ VĂN CHỦ",
        "{{NGAY_SINH}}": "15/08/1990",
        "{{SO_HO_CHIEU}}": "C12345678",
        "{{DIA_CHI_THUONG_TRU}}": "Hà Nội, Việt Nam",
    })

    # 2. Điền bảng danh sách động
    filler.apply_tables([
        TableRule(
            table_index=0,
            data_rows=[
                {"STT": "1", "Họ Tên": "Nguyễn Văn A", "Quan Hệ": "Bố", "Năm Sinh": "1960"},
                {"STT": "2", "Họ Tên": "Trần Thị B", "Quan Hệ": "Mẹ", "Năm Sinh": "1965"},
            ],
            delete_unused_template_rows=True,
            allow_break_across_pages=False,
        )
    ])

    # 3. Xuất kết quả
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
| **Immutable Template Guard** | `validate_output_path()` | `validate_output_path()` | Chặn ghi đè tệp template gốc, ném lỗi `TemplateProtectionError` |
| **Anti-Row Split** | `Row.AllowBreakAcrossPages = False` | `<w:trPr><w:cantSplit/></w:trPr>` | Ngăn không cho hàng bảng bị cắt ngang bởi trang in |
| **Prune Empty Rows** | `Row.Delete()` | `tr.getparent().remove(tr)` | Xóa các dòng template thừa khi số lượng item ít hơn số dòng mẫu |
| **Enforced Page Break** | `Paragraph.Format.PageBreakBefore = True` | `p.paragraph_format.page_break_before = True` | Đẩy các mục quan trọng (chữ ký, kết luận) sang trang mới |

---

## 4. Kiến Trúc Dual-Engine

- **Windows Native (`winword`):**
  - Tương tác In-Place Single-Pass trực tiếp trên Word DOM qua `win32com.client`.
  - Thay thế trường văn bản qua `Range.Find.Execute(Replace=wdReplaceOne)` để giữ 100% định dạng font.
  - Mở và lưu file `.doc` gốc mà không cần chuyển đổi trung gian.
  - Tự động đóng tài liệu và tắt tiến trình `WINWORD.EXE` trong khối `finally` an toàn.
- **Linux/Docker Fallback (`soffice`):**
  - Tự động kích hoạt trên các môi trường máy chủ Linux hoặc container Docker.
  - Thay thế Run-level thông minh, tránh gán thô bạo `p.text = ...` làm mất font formatting.
  - Sử dụng LibreOffice headless chuyển đổi `.doc` $\rightarrow$ `.docx`, thao tác XML bằng `python-docx`, sau đó chuyển đổi sang định dạng đích.

---

## 5. Cascading Vault Resolver & Bảo Mật PII (ADR-0059)

- Schema chuẩn hóa được định nghĩa tại: `.agents/skills/ccba-xu-ly-van-phong/templates/personal_profile.template.yaml`.
- Dữ liệu thực tế của người dùng **tuyệt đối không commit lên Git repository**.
- File thực tế được giải quyết tuần tự theo Cascading Vault Resolver:
  1. Spoke Local Vault: `./.md/knowledge/personal_profile.yaml` (dùng riêng cho spoke/hồ sơ hiện tại).
  2. Central User Vault: `~/.ccba/personal_profile.yaml` (dùng chung xuyên suốt các spoke trên máy trạm của kỹ sư).
  3. Môi trường: Biến môi trường `$CCBA_PERSONAL_VAULT`.

