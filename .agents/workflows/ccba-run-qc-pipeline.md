---
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn (Discovery -> Orchestrator).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# Workflow: Run QC Pipeline (Auto-Audit)

Workflow tự động hóa việc rà soát hồ sơ bản vẽ thiết kế, nhận diện cấu trúc, lập ma trận phối hợp và quét xung đột kỹ thuật đa bộ môn.

## Các bước thực hiện:

### Bước 1: Xác định thư mục dự án mục tiêu (Target Project)
1. Agent đọc tệp cấu hình `.md/workspace_context.yaml` hoặc phân tích ngữ cảnh làm việc để xác định đường dẫn thư mục dự án (`target_project`).
2. Nếu hệ thống nhận diện nhiều hơn 1 đường dẫn dự án đang mở, Agent bắt buộc phải dừng lại và yêu cầu người dùng lựa chọn dự án cần Audit.

### Bước 2: Kích hoạt chuỗi QC Pipeline (Execution)
Xác định đường dẫn Hub (`hub_path`) từ biến môi trường `CCBA_HUB_PATH` hoặc cấu hình Spoke và thực thi lần lượt các lệnh:

**A. Khám phá hồ sơ & Lập bản đồ dữ liệu (Discovery Engine)**
Chạy script Discovery để bóc tách thông tin bản vẽ PDF và tự động sinh ma trận phối hợp `Coordination_Matrix.csv`:
```bash
python "[hub_path]/.agents/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py" --target "[target_project]"
```

**B. Điều phối và Quét xung đột đồng thời (Batch Orchestrator)**
Chạy lệnh Orchestrator sử dụng ma trận vừa tạo để quét chéo các tầng kỹ thuật (mặc định Concurrency = 4):
```bash
python "[hub_path]/.agents/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py" --project-dir "[target_project]" --matrix "[target_project]/.md/extracts/discovery/Coordination_Matrix.csv" --out-dir "[target_project]/.md/extracts/audit_batch" --model "gemini-3.1-pro-low"
```

### Bước 3: Xem xét báo cáo
Sau khi chạy thành công, tệp báo cáo tổng hợp sẽ được ghi tại:
```text
[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md
```
Agent sử dụng `view_file` để trích xuất 50 dòng đầu tiên (chứa bảng Heat Map rủi ro) và hiển thị trực tiếp trong chat để Kỹ sư duyệt.
