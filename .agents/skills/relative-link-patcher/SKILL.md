---
name: relative-link-patcher
description: Sub-skill tự động sửa và chuẩn hóa liên kết tương đối của phụ lục (tích hợp trong ConversionPipeline).
role: sub_skill
master_skill: markdown-document-processing
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Sub-skill: Relative Link Patcher

Kỹ năng này chịu trách nhiệm sửa chữa các liên kết đứt gãy và đồng bộ cấu trúc thư mục liên kết tương đối giữa các tệp nghị định chính và các tệp phụ lục. Kỹ năng đã được **tích hợp tự động** vào Deep Seam `ConversionPipeline` ([`packages/mdconverter`](../../packages/mdconverter)).

---

## 1. Tích hợp Tự động trong Pipeline

Khi sử dụng `ConversionPipeline.convert()`, bộ vá liên kết tự động quét và điều chỉnh tiền tố `./appendices/` cho tất cả phụ lục trích xuất.

---

## 2. Lệnh CLI & Can thiệp Độc lập

Để quét và tự động chuẩn hóa liên kết phụ lục cho một tệp Markdown cụ thể:

```bash
python -m mdconverter.cli patch-links --file [đường_dẫn_tệp_markdown]
```

---

## 3. SOP Quy tắc đặt liên kết (SOP Rules)

Khi sửa đổi liên kết thủ công hoặc bằng mã nguồn, luôn tuân thủ:
1. **Tiền tố chuẩn:** Các liên kết phụ lục tại tệp nghị định chính phải bắt đầu bằng `./appendices/` thay vì `appendices/` hoặc đường dẫn tuyệt đối `file:///`.
   * *Đúng:* `[Phụ lục I](./appendices/nghi_dinh_217-phu_luc_01.md)`
   * *Sai:* `[Phụ lục I](appendices/nghi_dinh_217-phu_luc_01.md)`
2. **Đồng bộ Index:** Khi có phụ lục mới được thêm vào hoặc đổi tên, phải đồng bộ ngay sang tệp mục lục chính `index.md` và phân nhóm theo đúng Nghị định cha.
