# 🗺️ Bản Đồ Wayfinder: Chẩn Đoán Lỗi "User cancelled agent execution"

> **Mục tiêu:** Phân tích nguyên nhân gốc rễ (Root Cause) của lỗi giả lập "User cancelled agent execution" và thiết lập các rào chắn tự động nhằm triệt tiêu hiện tượng timeout/cancellation khi chạy kiểm thử.

---

## 🎯 1. Điểm Đích (Destination)

Xác định chính xác nguyên nhân phát sinh lỗi "User cancelled agent execution", thiết lập quy trình kiểm thử an toàn và tối ưu hóa thời gian chạy test suite để Agent không bao giờ bị ngắt kết nối giữa chừng.

---

## 🔍 2. Phân Tích Nguyên Nhân Gốc Rễ (Root Cause Analysis)

1. **Vượt ngưỡng thời gian chờ Tool Call (Command Timeout Boundary):**
   - Khi Agent chạy lệnh `pytest` không chỉ định file (`unscoped pytest`) trên toàn bộ thư mục `packages/ccba-legal-intel/tests` (74 unit tests), thời gian thực thi kéo dài trên 10-15 giây.
   - Hệ thống runtime hoặc IDE có ngưỡng timeout bảo vệ (ví dụ: `WaitMsBeforeAsync` hoặc server restart context reset), khiến tiến trình bị canceled và phát thông báo "User cancelled agent execution".

2. **Vi phạm Quy tắc Scoped Testing của CCBA Platform:**
   - Trong Hiến pháp [`AGENTS.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/AGENTS.md#4-execution-guardrails--async-task-policy) và Skill [`implement`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/implement/SKILL.md), quy tắc số 1 đã quy định rõ:
     > *"Nghiêm cấm Agent kích hoạt các lệnh kiểm thử toàn diện (unscoped pytest) trên cả repository mà không chỉ định rõ file test mục tiêu cụ thể."*

---

## 📝 3. Quyết Định Đã Chốt (Decisions so far)

- [x] **[Cấm Unscoped Pytest]** Tuyệt đối không chạy `pytest` trên cả thư mục lớn. Chỉ chạy duy nhất file test liên quan trực tiếp đến seam đang sửa (ví dụ: `pytest packages/ccba-legal-intel/tests/test_legal_pipeline_seam.py`).
- [x] **[Sử dụng Script An Toàn]** Luôn ưu tiên dùng `python scripts/safe_pytest.py -f <file_path>` hoặc chỉ định rõ file với `.venv\Scripts\pytest.exe <file_path>`.
- [x] **[Xử lý Async Task]** Khi cần chạy toàn bộ suite, bắt buộc chạy ngầm qua `WaitMsBeforeAsync: 5000` và kiểm tra kết quả qua `command_status` hoặc chờ hệ thống trả lời, không block phiên tương tác trực tiếp.

---

## 🚩 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

* 🚀 **[Ticket A: Scoped Test Enforcement in safe_pytest.py]** `[UNBLOCKED]`
  * *Mục tiêu:* Kiểm tra và cảnh báo chặn khi Agent vô tình gọi pytest không chỉ định file.
* 🚀 **[Ticket B: Fast Test Suite Tagging]** `[UNBLOCKED]`
  * *Mục tiêu:* Gắn nhãn `@pytest.mark.slow` cho các test case kết nối mạng/giả lập lâu, cho phép chạy `--quick` trong 1-2 giây.

---

## ⛔ 5. Rào Chắn Cưỡng Chế Cho Agent (Guardrails)

```powershell
# ✅ CHUẨN: Chạy duy nhất file test mục tiêu
.venv\Scripts\pytest.exe packages/ccba-legal-intel/tests/test_legal_pipeline_seam.py

# ❌ CẤM: Chạy cả thư mục test mà không chỉ định file
.venv\Scripts\pytest.exe packages/ccba-legal-intel/tests
```

---
*Tạo bởi CCBA Wayfinder System*
