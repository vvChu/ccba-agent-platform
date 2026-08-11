# Ticket #03: Viết Unit Test Kiểm chứng Safe Single-Instance Lock

**Bản đồ cha:** [map.md](./map.md)  
**Loại:** Task [AFK]  
**Trạng thái:** Mở (Bị chặn bởi Ticket #02)

---

## 🎯 Mục tiêu

Tạo unit test `tests/test_harness_lock.py` để khẳng định hàm `ensure_single_instance()` trong `scripts/run_harness_evals.py` hoạt động an toàn:
1. Không bao giờ bắn lệnh `taskkill` hoặc `proc.terminate()` lên PID hiện tại (`os.getpid()`) hoặc PID của tiến trình cha (`os.getppid()`).
2. Thực thi mượt mà không ném ngoại lệ ngay cả khi không có thư viện `psutil`.

---

## 📋 Các bước Thực thi

- [ ] Tạo file `tests/test_harness_lock.py`.
- [ ] Viết test case `test_ensure_single_instance_does_not_kill_self_or_parent()`.
- [ ] Chạy pytest kiểm chứng test pass 100%.
