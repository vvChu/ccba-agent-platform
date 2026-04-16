---
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn (Discovery -> Orchestrator).
---

# Workflow: Run QC Pipeline (Auto-Audit)

Workflow này được thiết kế để tự động lùng sục dữ liệu hồ sơ bản vẽ trong Project, tự tạo ma trận tọa độ không gian và gọi AI Gateway kiểm tra đụng độ các bộ môn trên tất cả các tầng kỹ thuật.

Người dùng có thể gọi qua lệnh:
```text
/run-qc-pipeline
```

## Các bước thực hiện

### Bước 1: Auto-Detect Không gian làm việc (Workspace Context)
1. Hãy quan sát và phân tích `<ADDITIONAL_METADATA>` để trích xuất đường dẫn Dự án (Project Directory) mà người dùng đang mở file code.
2. NẾU hệ thống phát hiện có MỘT đường dẫn duy nhất chứa biến `HSTK BVTC/` -> Gán nó thành `TARGET_PROJECT`.
3. NẾU hệ thống nhận diện thấy nhiều hơn 1 đường dẫn Workspace, hoặc đường dẫn không hợp chuẩn, **AI PHẢI DỪNG LẠI và đặt câu hỏi cho User chọn lựa:**
   - Ví dụ: _Tôi thấy bạn đang mở 2 dự án A và B, bạn muốn chạy Audit trên dự án nào?_
4. Đợi User chốt lệnh trước khi đi tới Bước 2.

### Bước 2: Kích hoạt Pipeline (Execution)

Gán biến `$TARGET_PROJECT` thành đường dẫn tuyệt đối của thư mục.

// turbo

**A. Chuẩn bị Dữ liệu (Discovery Engine)**
Chạy script Discovery để bóc dữ liệu PDF và sinh `Coordination_Matrix.csv`:

```bash
python "d:/GitHubProjects/ccba-agent-platform/.agent/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py" --target "$TARGET_PROJECT"
```

// turbo

**B. Điều phối và Quét Lỗi AI Đồng thời (Batch Orchestrator)**
Chạy lệnh Orchestrator với đầu vào là ma trận vừa tạo nhằm tiết kiệm thời gian (Concurrency = 4):

```bash
python "d:/GitHubProjects/ccba-agent-platform/.agent/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py" --project-dir "$TARGET_PROJECT" --matrix "$TARGET_PROJECT/.md/extracts/discovery/Coordination_Matrix.csv" --out-dir "$TARGET_PROJECT/.md/extracts/audit_batch" --model "gemini-3.1-pro-low"
```

### Bước 3: Xem Xét Báo Cáo
Sau khi 2 lệnh trên chạy thành công. Script cuối cùng sẽ tự sinh ra file Report Markdown tại `.md/extracts/audit_batch/BATCH_QC_Report_Auto.md`. 
AI Agent cần sử dụng Tool `view_file` để trích xuất 50 dòng đầu (Bảng Heat Map) và tóm tắt hiển thị trực tiếp trên giao diện Chat cho Kỹ sư duyệt.
