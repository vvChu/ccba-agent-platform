# Ticket 02: Gia Cố Vận Hành Git, Khóa An Toàn Flock & Dọn Dẹp Nhánh Rác Remote

- **Type:** Task (AFK / Code Implementation)
- **Status:** open
- **Assignee:** Unassigned
- **Target Seam:** `scripts/cron/run_nightly_tuner.sh`, `scripts/eval/doc_refactor_daemon.py`, `scripts/eval/nightly_tuner_daemon.py`
- **Reference:** Báo cáo nghiên cứu `/boost` ngày 18/09/2026 (REC-04, REC-05, REC-06)

---

## 🎯 Mục Tiêu
Bảo đảm hạ tầng Git tự động hóa hoạt động an toàn, chống chạy đè tiến trình, chặn đứng hiện tượng đẩy nhánh rỗng lên GitHub remote và dọn dẹp triệt để các nhánh rác mồ côi > 7 ngày.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết

### 1. Sửa `scripts/eval/doc_refactor_daemon.py`:
- [ ] **Chặn đẩy nhánh rỗng (Empty Push Guard):**
  - Chỉ gọi `git push` và `gh pr create` khi `report.commits_created > 0`.
  - Nếu `report.commits_created == 0`: Không gọi `git push`, tự động checkout trở lại và xóa nhánh rỗng cục bộ vừa tạo (`git branch -D branch_name`).

### 2. Sửa `scripts/cron/run_nightly_tuner.sh`:
- [ ] **Khóa đơn nhiệm (Process Mutex / Flock):**
  - Bổ sung cơ chế `flock -n 200` tại tệp `/tmp/ccba_nightly_runner.lock` ở đầu file. Nếu phát hiện tiến trình khác đang chạy, ghi log cảnh báo và thoát với exit code 0.
- [ ] **Export `PYTHONPATH` đầy đủ:**
  - Bổ sung `export PYTHONPATH="$PROJECT_ROOT/packages/ccba-harness/src:$PROJECT_ROOT/packages/ccba-ai/src:$PROJECT_ROOT:${PYTHONPATH:-}"` trước khi kích hoạt daemons.
- [ ] **Cách ly HEAD sạch giữa 2 Daemons:**
  - Sau khi `doc_refactor_daemon.py` hoàn thành, chạy lệnh `git checkout --detach "$TARGET_REF"` để đảm bảo `nightly_tuner_daemon.py` rẽ nhánh trực tiếp từ `TARGET_REF` sạch, không bị lồng nhánh con của doc-refactor.

### 3. Sửa `_cleanup_old_empty_branches` trong `scripts/eval/nightly_tuner_daemon.py`:
- [ ] **Đổi đối soát sang `origin/main`:**
  - Thay thế `git cherry main b` thành `git cherry origin/main b` để đối soát với remote ref thực tế thay vì local `main` có thể bị trôi dạt.
- [ ] **Mở rộng phạm vi dọn dẹp:**
  - Quét cả các nhánh tiền tố `docs/auto-refactor-*` bên cạnh `auto-tune/nightly-*`.
- [ ] **Dọn dẹp cả remote branch rỗng (nếu có PAT hỗ trợ):**
  - Bổ sung khối try-except xóa nhánh remote rỗng tương ứng (`git push origin --delete <branch>`) với cờ an toàn, không làm ngắt tiến trình nếu thiếu quyền.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. Thử nghiệm chạy liên tiếp 2 tiến trình `run_nightly_tuner.sh` song song: tiến trình thứ 2 lập tức dừng lại qua `flock` mà không gây tranh chấp index lock.
2. Chạy `doc_refactor_daemon.py` khi không có tài liệu nào cần sửa: Không có nhánh rác mới nào được đẩy lên GitHub remote.
3. Hàm `_cleanup_old_empty_branches` dọn dẹp thành công các nhánh rác tồn đọng > 7 ngày đối soát với `origin/main`.
4. Unit tests `scripts/tests/test_nightly_tuner_daemon.py` đạt 100% PASS.
