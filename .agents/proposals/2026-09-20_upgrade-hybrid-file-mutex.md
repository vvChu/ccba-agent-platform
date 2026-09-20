---
proposal_id: "2026-09-20_upgrade-hybrid-file-mutex"
type: "packages"
name: "upgrade-hybrid-file-mutex"
status: "proposed"
priority: "Cao"
proposed_by_project: "vvc-second-brain-scripts"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-20"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
  - "Concurrency & Harness Infrastructure"
---

# RFC Proposal: Nâng Cấp Hybrid FileMutexLock Cho `ccba-harness`

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`vvc-second-brain-scripts`)
- **Ngày lập:** 2026-09-20
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý & kỹ thuật:** [ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0058](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0058-automation-first-quality-and-deterministic-hard-completion-lock.md), Quy chế Tổ chức CCBA 2026.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain point):**
   Trong các pipeline xử lý đa tiến trình và daemon nền (như crawler VIP TVPL, đa tác vụ `ccba-ai` Team/Plan, OCR watchdog), cơ chế tạo file độc quyền cũ (`open(..., "x")`) gặp phải rủi ro chí mạng: **Stale Lock khi tiến trình bị crash đột ngột (unhandled exception, SIGKILL / Terminate, mất điện)**.
   Khi đó, file lock vẫn còn trên đĩa chứa timestamp cũ, buộc các tiến trình tiếp theo phải chờ hết thời gian hết hạn (`expire_seconds = 300s` / 5 phút) mới có thể chiếm lại quyền ghi, gây nghẽn toàn bộ pipeline và vi phạm tính liên tục của hệ thống 24/7.

2. **Quá trình ươm tạo & giải pháp đúc rút tại Spoke (`vvc-second-brain-scripts`):**
   Tại Spoke, chúng tôi đã hoàn thiện cơ chế khóa tệp đa tiến trình/đa luồng cấp nhân OS (`msvcrt.locking` trên Windows và `fcntl.flock` trên POSIX). Khi tiến trình chết đột ngột, Kernel OS tự động thu hồi và giải phóng file descriptor trong mili-giây, cho phép các tiến trình khác thu hồi quyền khóa ngay lập tức (Zero-Stale-Lock).

3. **Giá trị khi phổ biến lên Hub:**
   Nâng cấp trực tiếp Public Deep Seam `FileMutexLock` trong `packages/ccba-harness/src/ccba_harness/_mutex.py`. Toàn bộ hệ sinh thái Hub (`ccba-ai`, `ccba-legal-intel`, các background runners) được hưởng lợi trực tiếp:
   - Thu hồi khóa tức thì khi crash (< 200ms thay vì 300s).
   - Bảo đảm 100% tương thích ngược (Backward Compatibility) với các synthetic lock tests của `ccba-legal-intel`.
   - Ngăn chặn triệt để lỗi Windows Mandatory Lock Violation thông qua kỹ thuật **High-Offset Locking (`_LOCK_BYTE_OFFSET = 0x7FFFFFFF`)**.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Triệt tiêu thời gian nghẽn 5 phút khi crash, bảo đảm tính sẵn sàng 24/7 của toàn bộ daemons |
| **Độ Phức tạp (Complexity)** | Thấp (KISS) | 100% Python stdlib (`msvcrt`, `fcntl`, `os`, `json`), không cài thêm thư viện thứ 3 |
| **Bảo vệ Windows Concurrency** | Đạt 100% | High-Offset Locking ($2\text{GB}-1$) cho phép đọc JSON metadata mà không bị `PermissionError` |
| **Bất biến Tái sử dụng** | Đạt 100% | Reset triệt để `_fd = None`, `is_locked = False`, `_thread_lock_acquired = False` trong `release()` |
| **Rủi ro Rò rỉ (Leakage)** | 0 vi phạm | Vượt qua `check_spoke_leakage.py` |

---

### 3. Thiết Kế Deep Seams & Đặc Tả Kỹ Thuật tại Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub Monorepo:**
   - Mã nguồn: [`packages/ccba-harness/src/ccba_harness/_mutex.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/_mutex.py)
   - Bộ kiểm thử mới: [`packages/ccba-harness/tests/test_mutex_hybrid.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/tests/test_mutex_hybrid.py)
   - Public Seam export: `from ccba_harness import FileMutexLock` (giữ nguyên hợp đồng giao diện hiện có).

2. **Giao diện công khai (Public Interface):**
   ```python
   class FileMutexLock:
       """A process-aware and expiration-safe hybrid file-based mutual exclusion lock."""

       def __init__(
           self,
           lock_path: Path,
           timeout: float = 10.0,
           retry_interval: float = 0.1,
           expire_seconds: float = 300.0,
       ) -> None: ...

       def acquire(self) -> FileMutexLock:
           """Acquire lock via Thread lock + Kernel OS lock + JSON metadata."""
           ...

       def release(self) -> None:
           """Release OS lock, close descriptor, unlink file, and reset instance state."""
           ...

       def __enter__(self) -> FileMutexLock:
           return self.acquire()

       def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
           self.release()
   ```

---

### 4. Quy Trình Thẩm Định & Kết Quả Kiểm Thử (Verification Log)

Toàn bộ 5 cổng kiểm thử đã được chạy thực tế và đạt kết quả tuyệt đối:

1. **Cổng 1 (Downstream `ccba-ai`):**
   - Lệnh: `pytest packages/ccba-ai/tests/test_plan_manager.py packages/ccba-ai/tests/test_team.py`
   - Kết quả: **6/6 passed in 2.84s**
2. **Cổng 2 (Downstream `ccba-legal-intel`):**
   - Lệnh: `pytest packages/ccba-legal-intel/tests/test_crawler_upgrades.py packages/ccba-legal-intel/tests/test_crawler_adversarial_challenger.py -k "test_mutex"`
   - Kết quả: **6/6 passed in 15.77s**
3. **Cổng 3 (Hybrid Mutex Test Suite):**
   - Lệnh: `pytest packages/ccba-harness/tests/test_mutex_hybrid.py`
   - Kết quả: **7/7 passed in 6.07s** (bao gồm test tái sử dụng instance, đọc JSON dưới lock, subprocess crash recovery < 0.5s)
4. **Cổng 4 (Code Quality & Formatting):**
   - Lệnh: `python -m ruff check` & `python -m ruff format --check`
   - Kết quả: **All checks passed!**
5. **Cổng 5 (Governance & Spoke Leakage):**
   - Lệnh: `python scripts/governance/check_spoke_leakage.py` & `compile_catalog.py`
   - Kết quả: **0 violations, 0 warnings. Catalog compiled successfully.**

---

### 5. Cam Kết Bất Biến về Bảo Tồn Kỹ Năng & Tương Thích Ngược
- Toàn bộ các downstream consumers hiện tại (`ccba-ai/services/plan.py`, `ccba-ai/services/team.py`, `ccba-legal-intel/session.py`) hoàn toàn không phải thay đổi bất kỳ dòng code nào.
- Các bài test synthetic lock (`test_mutex_held_timeout`) tiếp tục hoạt động chính xác 100%.
