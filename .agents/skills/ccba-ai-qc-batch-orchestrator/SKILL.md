---
name: CCBA AI QC Batch Orchestrator
description: Điều phối quá trình quét Audit chất lượng hồ sơ thiết kế (QC) đa bộ môn (Arch, KC, MEP, PCCC) trên quy mô lớn, thao tác hàng loạt qua file Coordination Matrix.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Batch Orchestrator

**Batch Orchestrator** tự động hóa dây chuyền kiểm soát chất lượng (QC Workflow) khi có nhiều danh mục hồ sơ hoặc nhiều tầng kỹ thuật cần kiểm tra. Lớp này điều phối song song các cuộc gọi AI để kiểm tra xung đột đa bộ môn (Multidisciplinary Audit), giúp tiết kiệm 90% thời gian chạy máy.

---

## Hướng dẫn sử dụng

Dữ liệu đầu vào của Orchestrator dựa trên file ma trận `Coordination_Matrix.csv` được sinh tự động bởi skill `ccba-ai-qc-discovery`.

### Lệnh chạy:
```bash
python .agents/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py --project-dir "[project_dir]" --matrix ".md/extracts/discovery/Project_Coordination_Matrix.csv" --concurrency 4
```

---

## Kiến trúc Hoạt động (Internal Logic)

1. **Parser Module:** Phân tích cột `NormalizedLevel` và danh sách các tệp tin bản vẽ tương ứng trong `Coordination_Matrix.csv`.
2. **Missing Document Handler:** Nếu một cấu kiện bị thiếu sheet, hoặc không tìm thấy trang thực tế thì tự động sinh ra một khung ảnh trắng `blank.png` làm fallback để tránh ngắt quãng pipeline.
3. **Async Batcher:** Quản lý hàng chờ tác vụ (Task Queue), thực thi song song các cuộc gọi Quad-View (L01, L02...) lên AI Gateway.
4. **Integration Handoff:** Chuyển kết quả phân tích JSON về cho `IDOPReporter` để biên soạn thành báo cáo Markdown/Docx hoàn chỉnh.
