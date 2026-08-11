# Ticket #02: Bổ sung Subprocess Timeout & Phân đoạn Gate trong `run_harness_evals.py`

**Bản đồ cha:** [map.md](./map.md)  
**Loại:** Task [AFK]  
**Trạng thái:** Mở (Frontier)

---

## 🎯 Mục tiêu

Cải tiến `scripts/run_harness_evals.py` để hỗ trợ:
1. Tham số `--gate <name>` (cho phép chạy riêng từng gate như `docs`, `stats`, `pytest`, `syntax`).
2. Mặc định gán `timeout=30` cho mỗi `subprocess.run()` để tránh tình trạng tiến trình con bị treo quá 30 giây làm trigger ngắt kết nối `User cancelled agent execution`.

---

## 📋 Các bước Thực thi

- [ ] Cập nhật `argparse` trong `scripts/run_harness_evals.py` bổ sung tùy chọn `--gate`.
- [ ] Thêm `timeout=30` vào các lệnh `subprocess.run()` bên trong các hàm kiểm tra gate.
- [ ] Bắt exception `subprocess.TimeoutExpired` để in thông báo rõ ràng thay vì treo tiến trình.
