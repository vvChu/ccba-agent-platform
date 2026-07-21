---
name: relative-link-patcher
description: Sub-skill tự động sửa và chuẩn hóa các liên kết tương đối của phụ lục (tiền tố ./appendices/) trong file Markdown chính và đồng bộ mục lục index.md.
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

Kỹ năng này chịu trách nhiệm sửa chữa các liên kết đứt gãy và đồng bộ cấu trúc thư mục liên kết tương đối giữa các tệp nghị định chính và các tệp phụ lục.

## Lệnh CLI Tự động
Để quét và tự động chuẩn hóa liên kết phụ lục:
```bash
python -m mdconverter.cli patch-links --file [đường_dẫn_tệp_markdown]
```

## SOP Quy tắc đặt liên kết (SOP Rules)
Khi sửa đổi liên kết thủ công hoặc bằng mã nguồn, luôn tuân thủ:
1. **Tiền tố chuẩn:** Các liên kết phụ lục tại tệp nghị định chính phải bắt đầu bằng `./appendices/` thay vì `appendices/` hoặc đường dẫn tuyệt đối `file:///`.
   * *Đúng:* `./appendices/nghi_dinh_217-phu_luc_01.md`
   * *Sai:* `appendices/nghi_dinh_217-phu_luc_01.md`
2. **Đồng bộ Index:** Khi có phụ lục mới được thêm vào hoặc đổi tên, phải đồng bộ ngay sang tệp mục lục chính [index.md](../../../.md/legal_docs/luat_xay_dung_2025_so_135_2025_qh15/index.md) và phân nhóm theo đúng Nghị định cha.
