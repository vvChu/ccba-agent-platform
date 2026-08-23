# 🎫 Ticket 02: CI Gate Kiểm Tra Dead-Link Trong Global Skills

## 🎯 Mục Tiêu (Goal)
Tạo tệp kiểm thử tự động `tests/governance/test_global_skills_integrity.py`:
1. Quét tệp cấu hình toàn cục `C:\Users\chuvu\.gemini\config\skills\ccba-platform\SKILL.md` (nếu tồn tại).
2. Trích xuất tất cả các liên kết có định dạng `[hub_path]/...` hoặc đường dẫn file tương đối/tuyệt đối.
3. Kiểm tra sự tồn tại thực tế của các tệp đích trên ổ đĩa Hub.
4. Đảm bảo mọi mục menu từ 1 đến 16 đều trỏ tới tệp workflow/skill đang hoạt động.

## 🛠️ Yêu Cầu Kỹ Thuật
- Chạy bằng `pytest tests/governance/test_global_skills_integrity.py`.
- Không phụ thuộc cứng vào user path (sử dụng Hub root hiện tại để resolve `[hub_path]`).
- Đạt 100% `mypy` và `ruff`.
