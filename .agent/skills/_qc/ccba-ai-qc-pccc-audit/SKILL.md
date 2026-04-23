---
name: ccba-ai-qc-pccc-audit
description: Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông qua cơ chế Semantic Map-Reduce.
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
bundle: "_qc"
---

# Kỹ năng (Skill): Semantic PCCC Audit

Skill này sử dụng cơ chế Semantic Map-Reduce để băm nhỏ, phân tích chéo và gộp kết quả đánh giá kỹ thuật đối với một bộ hồ sơ PCCC lớn, giúp khắc phục giới hạn token của LLM cục bộ (Context window limit) và hiện tượng sinh ảo giác (hallucination).

## Cơ chế hoạt động (Map-Reduce)

1. **Package 1 (Legal & Specs):** Đánh giá Thuyết minh PCCC với Quy chuẩn QCVN 06:2022/BXD và TCVN 3890:2023. Kiểm tra việc cập nhật ý kiến của Cơ quan Công an.
2. **Package 2 (MEP Water):** So sánh chéo thông số thiết bị (bể nước, bơm chữa cháy, Sprinkler) giữa Bản vẽ MEP và Thuyết minh.
3. **Package 3 (MEP Alarm vs Arch):** So sánh chéo sơ đồ Báo cháy MEP và Bản vẽ Kiến trúc (vị trí đầu báo, đèn sự cố, lối thoát nạn).
4. **Reducer:** Tổng hợp các findings (lỗi) từ 3 gói trên, loại bỏ trùng lặp và xuất thành báo cáo Markdown hoàn chỉnh (phù hợp nộp Mẫu PC13 theo NĐ 105/2025/NĐ-CP).

## Cấu trúc Command Line Interface (CLI)

Agent sử dụng script `scripts/audit_engine.py` để thực thi. 

### Các tham số bắt buộc (Đường dẫn đến file nội dung dạng Markdown/Text):
*   `--tm`: Đường dẫn đến file nội dung Thuyết minh PCCC.
*   `--arch`: Đường dẫn đến file nội dung Bản vẽ Kiến trúc PCCC.
*   `--mep`: Đường dẫn đến file nội dung Bản vẽ MEP PCCC.
*   `--gopy`: Đường dẫn đến file nội dung Góp ý/Thẩm duyệt của PC07 (Nếu không có, truyền một chuỗi rỗng hoặc file trống).

### Các tham số tuỳ chọn:
*   `--model`: Chỉ định model LLM sử dụng (Mặc định: `qwen-local-primary`). Có thể sử dụng `gpt-4o` hoặc các model khác hỗ trợ trên Gateway.
*   `--out`: Tên file hoặc đường dẫn file Báo cáo xuất ra (Mặc định: `PCCC_MapReduce_Report.md`).

## Hướng dẫn sử dụng cho Agent

Khi cần kiểm tra/audit một bộ hồ sơ PCCC, Agent cần thực hiện:

1. Đảm bảo toàn bộ hồ sơ PDF đã được chạy qua module `ccba-ai-pdf-preprocessor` (trích xuất text/vector) hoặc lưu dưới dạng văn bản `.md`.
2. Chạy lệnh python:
```powershell
python "D:\GitHubProjects\ccba-agent-platform\.agent\skills\_qc\ccba-ai-qc-pccc-audit\scripts\audit_engine.py" `
    --tm "đường/dẫn/đến/thuyet_minh.md" `
    --arch "đường/dẫn/đến/kien_truc.md" `
    --mep "đường/dẫn/đến/mep.md" `
    --gopy "đường/dẫn/đến/pc07.md" `
    --model "qwen-local-primary" `
    --out "Bao_Cao_Tham_Dinh_PCCC.md"
```
3. Đọc nội dung file kết quả xuất ra và tóm tắt lại cho Người dùng (User).
