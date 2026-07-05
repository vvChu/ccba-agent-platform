---
name: ccba_run_qc_pipeline
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn (Discovery -> Orchestrator -> Báo cáo).
disable-model-invocation: true
---

# Quy trình Chạy QC Pipeline Tự động (Run QC Pipeline)

Kỹ năng này điều phối việc thực thi toàn trình chuỗi kiểm soát chất lượng hồ sơ thiết kế bản vẽ qua 3 giai đoạn: Nhận diện cấu trúc, Quét xung đột đồng thời, và Xuất báo cáo tổng hợp.

## Các bước thực hiện:

1. **Xác định thư mục dự án mục tiêu (Target Project Check)**:
   - Đọc tệp cấu hình `.md/workspace_context.yaml` để lấy đường dẫn dự án (`target_project`).
   - Nếu có nhiều đường dẫn dự án đang hoạt động, yêu cầu người dùng chỉ định.
   - **Tiêu chí hoàn thành:** Xác định duy nhất một đường dẫn thư mục dự án đích hợp lệ và kiểm tra thư mục này có tồn tại cục bộ.

2. **Kích hoạt chuỗi QC Pipeline (Pipeline Execution)**:
   - Xác định đường dẫn Hub (`hub_path`) từ biến môi trường `CCBA_HUB_PATH` hoặc cấu hình Spoke.
   - Thực thi tuần tự hai lệnh sau:
     * **Discovery Engine** (Bóc tách PDF bản vẽ và sinh ma trận phối hợp):
       ```bash
       python "[hub_path]/.agents/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py" --target "[target_project]"
       ```
     * **Batch Orchestrator** (Quét xung đột đa bộ môn theo ma trận):
       ```bash
       python "[hub_path]/.agents/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py" --project-dir "[target_project]" --matrix "[target_project]/.md/extracts/discovery/Coordination_Matrix.csv" --out-dir "[target_project]/.md/extracts/audit_batch" --model "gemini-3.1-pro-low"
       ```
   - **Tiêu chí hoàn thành:** Cả hai lệnh chạy thành công không có lỗi hệ thống, sinh ra tệp ma trận và kết quả quét tại thư mục đầu ra đích.

3. **Trình bày Báo cáo Tổng hợp (Report Review)**:
   - Truy cập và đọc tệp báo cáo tổng hợp tại:
     `[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md`
   - Sử dụng `view_file` trích xuất 50 dòng đầu tiên (chứa bảng Heat Map đánh giá rủi ro) và hiển thị trực tiếp trong cuộc hội thoại để Kỹ sư xem xét.
   - **Tiêu chí hoàn thành:** Bảng Heat Map rủi ro từ báo cáo được hiển thị rõ ràng trên giao diện chat cho người dùng kiểm tra.

## Tiêu chuẩn Thực thi (Best Practices)

- **Định danh đường dẫn:** Luôn sử dụng dấu ngoặc kép bọc quanh các biến đường dẫn (`[hub_path]`, `[target_project]`) để tránh lỗi khoảng trắng trên hệ thống Windows.
- **Xử lý lỗi:** Nếu lệnh Discovery hoặc Orchestrator bị lỗi, dừng ngay pipeline và in chi tiết mã lỗi để Kỹ sư xử lý.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
