---
name: CCBA AI QC Batch Orchestrator
description: Điều phối quét Audit chất lượng hồ sơ thiết kế đa bộ môn qua Quad-View (Pha 2 của QCAuditPipeline).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Batch Orchestrator

Kỹ năng này điều phối song song các cuộc gọi AI Vision để kiểm tra xung đột đa bộ môn (Kiến trúc, Kết cấu, MEP, PCCC) theo cơ chế Quad-View dựa trên ma trận phối hợp. Đây là **Pha 2** trong Deep Seam **`QCAuditPipeline`** ([`packages/ccba-ai`](../../packages/ccba-ai)).

---

## Hướng dẫn Sử dụng

Khi chạy trong `QCAuditPipeline`, dữ liệu ma trận được truyền trực tiếp từ Discovery Engine.

### Lệnh chạy Độc lập:
```bash
python .agents/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py --project-dir "[project_dir]" --matrix ".md/extracts/discovery/Coordination_Matrix.csv" --concurrency 4
```

---

## Kiến trúc Hoạt động (Internal Logic)

1. **Parser Module:** Phân tích cột `NormalizedLevel` và danh sách các tệp tin bản vẽ tương ứng trong `Coordination_Matrix.csv`.
2. **Missing Document Handler:** Nếu một cấu kiện bị thiếu sheet, hoặc không tìm thấy trang thực tế thì tự động sinh ra một khung ảnh trắng `blank.png` làm fallback để tránh ngắt quãng pipeline.
3. **Async Batcher:** Quản lý hàng chờ tác vụ (Task Queue), thực thi song song các cuộc gọi Quad-View (L01, L02...) lên AI Gateway.
4. **Integration Handoff:** Chuyển kết quả phân tích JSON về cho Reporter Engine để biên soạn thành báo cáo Markdown/Docx hoàn chỉnh.
