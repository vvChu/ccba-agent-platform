# Danh sách Ticket Chi Tiết: Automated Operational Guardrails

**Mã bản đồ**: `issue-automated-operational-guardrails`
**Đường dẫn bản đồ**: [map.md](map.md)

---

## ✅ Ticket 1: Triển khai Pytest Pre-Execution Enforcement Hook (`conftest.py`)

- **Mã Ticket**: `ticket-auto-guard-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[MODIFY] conftest.py` (Project Root)
- **Mục tiêu**:
  - Viết hook `pytest_cmdline_main(config)` trong `conftest.py`.
  - Nếu không truyền đối số file hoặc bằng `["."]`, in thông báo cảnh báo rõ ràng và ngắt tiến trình với mã thoát `1`.
  - Nếu có tham số file (ví dụ `pytest tests/test_xxxx.py`), cho phép tiếp tục chạy bình thường.

---

## ✅ Ticket 2: Xây dựng Auto-Wrapper CLI Script (`scripts/safe_pytest.py`)

- **Mã Ticket**: `ticket-auto-guard-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[NEW] scripts/safe_pytest.py`
- **Mục tiêu**:
  - Tạo script CLI hỗ trợ nhận diện file test tự động từ `git status`.
  - Tự động chuyển đổi và gọi `python scripts/safe_runner.py --command "pytest <target>"`.
  - Đảm bảo có chế độ `--dry-run` để kiểm tra câu lệnh trước khi thực thi.

---

## ✅ Ticket 3: Đồng bộ hóa Mẫu lệnh trong Core Skills & Workflows

- **Mã Ticket**: `ticket-auto-guard-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**:
  - `[MODIFY] .agents/skills/eval-gate/SKILL.md`
  - `[MODIFY] .agents/skills/implement/SKILL.md`
  - `[MODIFY] .agents/skills/tdd/SKILL.md`
- **Mục tiêu**:
  - Cập nhật tất cả các ví dụ lệnh và hướng dẫn thực thi test trong các skill core để ưu tiên sử dụng `safe_pytest.py`.

---

## ✅ Ticket 4: Kiểm thử Tự động hóa (Validation & Stress-Test)

- **Mã Ticket**: `ticket-auto-guard-4`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Mục tiêu**:
  - Thử nghiệm chạy lệnh `pytest` không đối số $\rightarrow$ Xác nhận bị chặn bởi `conftest.py`.
  - Thử nghiệm chạy `python scripts/safe_pytest.py` $\rightarrow$ Xác nhận test pass và log lưu đầy đủ tại `.md/scratch/exec_log.txt`.

