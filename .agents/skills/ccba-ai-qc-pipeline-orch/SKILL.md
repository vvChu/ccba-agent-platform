---
name: ccba-ai-qc-pipeline-orch
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn (Discovery -> Orchestrator -> Báo cáo).
disable-model-invocation: true
category: utilities
keywords: [qc, pipeline, orchestrator, automatic-audit]
metadata:
  author: CCBA
  version: "2.0.0"
---

# Quy trình Chạy QC Pipeline Tự động (Run QC Pipeline)

Kỹ năng này điều phối việc thực thi toàn trình chuỗi kiểm soát chất lượng hồ sơ thiết kế bản vẽ qua Deep Seam **`QCAuditPipeline`** ([`packages/ccba-ai`](../../packages/ccba-ai)) qua 3 giai đoạn tự động: Nhận diện cấu trúc (Discovery), Quét xung đột đồng thời (Quad-View Audit), và Xuất báo cáo tổng hợp (Reporter).

---

## Các bước thực hiện:

1. **Xác định thư mục dự án mục tiêu (Target Project Check)**:
   - Đọc tệp cấu hình `.md/workspace_context.yaml` để lấy đường dẫn dự án (`target_project`).
   - Nếu có nhiều đường dẫn dự án đang hoạt động, yêu cầu người dùng chỉ định.
   - **Tiêu chí hoàn thành:** Xác định duy nhất một đường dẫn thư mục dự án đích hợp lệ và kiểm tra thư mục này có tồn tại cục bộ.

2. **Kích hoạt chuỗi QC Pipeline qua Deep Seam (`QCAuditPipeline`)**:
   - Sử dụng Python API hoặc Script điều phối thống nhất:
     ```python
     import asyncio
     from ccba_ai import QCAuditPipeline

     pipeline = QCAuditPipeline()
     summary = asyncio.run(pipeline.run_audit(
         project_dir="[target_project]",
         output_dir="[target_project]/.md/extracts/audit_batch"
     ))
     ```
     Hoặc qua CLI:
     ```bash
     python -m ccba_ai.cli run-qc --project "[target_project]" --out-dir "[target_project]/.md/extracts/audit_batch"
     ```
   - Deep Seam tự động xâu chuỗi:
     * **Discovery**: Bóc tách danh mục PDF bản vẽ và sinh ma trận phối hợp `Coordination_Matrix.csv`.
     * **Audit Engine**: Quét đối soát đa bộ môn (Kiến trúc, Kết cấu, MEP, PCCC) theo cơ chế Quad-View.
     * **Reporter Engine**: Biên tập và tổng hợp báo cáo kỹ thuật Heat Map.
   - **Tiêu chí hoàn thành:** Pipeline chạy hoàn tất không có lỗi hệ thống, sinh ra tệp ma trận và báo cáo tổng hợp tại thư mục đầu ra.

3. **Trình bày Báo cáo Tổng hợp (Report Review)**:
   - Truy cập và đọc tệp báo cáo tổng hợp tại:
     `[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md` (hoặc `qc_audit_report.md`).
   - Sử dụng `view_file` trích xuất phần tóm tắt rủi ro và Heat Map hiển thị trực tiếp trong cuộc hội thoại để Kỹ sư xem xét.
   - **Tiêu chí hoàn thành:** Bảng Heat Map rủi ro từ báo cáo được hiển thị rõ ràng trên giao diện chat cho người dùng kiểm tra.

---

## Tiêu chuẩn Thực thi (Best Practices)

- **Định danh đường dẫn:** Luôn sử dụng dấu ngoặc kép bọc quanh các biến đường dẫn (`[target_project]`) để tránh lỗi khoảng trắng trên hệ thống Windows.
- **Xử lý lỗi:** Nếu quá trình Discovery hoặc Audit phát hiện thiếu sheet, hệ thống tự động chèn khung hình nền fallback và tiếp tục tiến trình mà không làm gián đoạn toàn bộ batch.
