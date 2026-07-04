---
name: ccba-ai-qc-pccc-audit
description: Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông qua cơ chế Semantic Map-Reduce.
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
bundle: "_qc"
---

# CCBA AI QC PCCC Audit

Skill này sử dụng cơ chế **Semantic Map-Reduce** để phân tích chéo và gộp kết quả đánh giá kỹ thuật đối với hồ sơ PCCC lớn, giúp khắc phục giới hạn context window của LLM và hiện tượng sinh ảo giác.

---

## Quy trình Map-Reduce

1. **Map 1 (Legal & Specs):** Đánh giá thuyết minh PCCC dựa trên quy chuẩn QCVN 06:2022/BXD, TCVN 3890:2023 và phản hồi của PC07.
2. **Map 2 (MEP Water):** So sánh chéo thông số thiết bị chữa cháy giữa bản vẽ MEP và thuyết minh.
3. **Map 3 (MEP Alarm vs Arch):** So sánh sơ đồ báo cháy và bản vẽ kiến trúc (vị trí đầu báo, đèn sự cố, lối thoát nạn).
4. **Reduce:** Tổng hợp các lỗi phát hiện được, loại bỏ trùng lặp và xuất thành báo cáo Markdown hoàn chỉnh theo mẫu PC13 (NĐ 105/2025/NĐ-CP).

---

## Hướng dẫn Vận hành

### 1. Điều kiện tiền quyết
Toàn bộ tài liệu PDF phải được chạy qua `ccba-ai-pdf-preprocessor` để chuyển đổi sang định dạng văn bản `.md`.

### 2. Lệnh chạy script:
Xác định đường dẫn Hub (`hub_path`) và chạy lệnh:
```bash
python "[hub_path]/.agents/skills/ccba-ai-qc-pccc-audit/scripts/audit_engine.py" \
    --tm "đường/dẫn/đến/thuyet_minh.md" \
    --arch "đường/dẫn/đến/kien_truc.md" \
    --mep "đường/dẫn/đến/mep.md" \
    --gopy "đường/dẫn/đến/pc07.md" \
    --model "qwen-local-primary" \
    --out "Bao_Cao_Tham_Dinh_PCCC.md"
```
*(Nếu không có văn bản góp ý của PC07, truyền một chuỗi rỗng `--gopy ""`)*
