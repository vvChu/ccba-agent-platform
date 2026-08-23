# Danh sách Ticket Chi Tiết: Triển Khai Tầng 5 (Production Log Mining & Auto-Tuning Evals)

**Mã bản đồ**: `issue-5-layer-eval-log-mining`  
**Đường dẫn bản đồ**: [map.md](map.md)  

---

## 🟢 Ticket 5.1: Thiết kế Schema & Core Parser cho `log_eval_miner.py`

- **Mã Ticket**: `ticket-log-miner-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Tệp tin tác động**: `[NEW] scripts/log_eval_miner.py`
- **Mục tiêu**:
  - Viết CLI script `scripts/log_eval_miner.py` đọc các tệp `transcript.jsonl` từ `.system_generated/logs/` hoặc thư mục log tùy chọn.
  - Bóc tách toàn bộ `USER_INPUT` prompts.
  - Áp dụng biểu thức chính quy / logic `maskara-privacy` để tự động lọc và redact thông tin cá nhân (tên riêng, số điện thoại, API keys, tên dự án nhạy cảm).

---

## 🟡 Ticket 5.2: Thuật toán nhận diện Router Failures & Disclaimer Mismatches

- **Mã Ticket**: `ticket-log-miner-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by `ticket-log-miner-1`
- **Tệp tin tác động**: `[MODIFY] scripts/log_eval_miner.py`
- **Mục tiêu**:
  - Phân tích chuỗi phản hồi `PLANNER_RESPONSE` tương ứng với mỗi `USER_INPUT`.
  - Nhận diện các câu hỏi khiến Agent trả về Disclaimer khước từ hoặc gọi sai skill tool.
  - Tự động đóng gói các `USER_INPUT` này thành Negative/Happy Test Cases chuẩn 4 tầng và lưu vào `.agents/skills/eval-gate/test_cases/eval_<skill>.json`.

---

## 🟡 Ticket 5.3: Tích hợp CLI Runner & Unit Tests cho Miner

- **Mã Ticket**: `ticket-log-miner-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by `ticket-log-miner-1`, `ticket-log-miner-2`
- **Tệp tin tác động**: 
  - `[NEW] scripts/tests/test_log_eval_miner.py`
  - `[MODIFY] .agents/skills/eval-gate/scripts/eval_runner.py`
- **Mục tiêu**:
  - Viết Unit Tests kiểm thử 100% chức năng parse, redact và auto-generate cho `log_eval_miner.py` trong `scripts/tests/test_log_eval_miner.py`.
  - Bổ sung flag `--mine-logs` vào `eval_runner.py` để hỗ trợ tự động đào log trước khi chạy evals.
  - Kiểm tra 100% pass qua `python scripts/safe_pytest.py -f scripts/tests/test_log_eval_miner.py`.
