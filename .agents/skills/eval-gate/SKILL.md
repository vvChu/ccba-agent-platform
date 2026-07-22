---
name: eval-gate
description: Thực hiện kiểm chứng mã nguồn thông qua CI Gates tự động và tự động sửa lỗi (Self-Healing Loop).
---

# 🛡️ Kỹ năng: eval-gate (Tự kiểm chứng & Sửa lỗi)

Kỹ năng này bọc script `scripts/run_harness_evals.py` và chịu trách nhiệm bảo vệ codebase khỏi các lỗi cú pháp, kiểu dữ liệu, test cases thất bại hoặc tài liệu bị ảo ảnh.

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Chạy kiểm định tự động & Auto-Tuning
Kích hoạt chạy script điều phối chính bằng lệnh Python:
```bash
python scripts/run_harness_evals.py

# KHOANH VÙNG TEST (Scoped Test Execution): Chạy file test cụ thể để tiết kiệm thời gian và tránh treo task
.venv\Scripts\pytest -q tests/test_agent_execution_guardrails.py

# Tự động tối ưu hóa SKILL.md với Skill Auto-Tuner (SkillOpt loop)
python .agents/skills/eval-gate/scripts/eval_runner.py --skill [tên-skill] --auto-tune --max-iterations 3
```
*(Nếu bạn chỉ muốn kiểm tra định dạng/cú pháp mà không chạy test, bạn có thể truyền `--no-test`. Lưu ý `run_harness_evals.py` đã tự động tích hợp Singleton Process Lock và Pre-Eval Health Check để ngăn ngừa ngốn 100% CPU).*

### Bước 2: Đánh giá kết quả
*   **Nếu exit code = 0 (Tất cả Gate PASS):** Codebase sạch sẽ, bạn có thể yên tâm bàn giao/commit/tạo PR.
*   **Nếu exit code = 1 (Có Gate bị FAILED):** Đọc báo cáo lỗi tổng hợp ở cuối đầu ra của script. 

### Bước 3: Vòng lặp tự chữa lỗi (Self-Healing Loop)
Nếu phát hiện Gate bị thất bại:
1.  Đọc kỹ log chi tiết của Gate bị lỗi. Tránh phỏng đoán, hãy đọc trực tiếp dòng thông báo lỗi (Traceback) được in ra.
2.  Xác định file và dòng code gây lỗi.
3.  Thực hiện sửa đổi trực tiếp lên file lỗi theo nguyên tắc **KISS** (chỉnh sửa nhỏ nhất để sửa lỗi, không refactor lan man).
4.  Quay lại **Bước 1** để chạy lại kiểm tra.
5.  **Giới hạn (Retry Cap):** Chỉ lặp lại tối đa **3 lần**. Nếu sau 3 lần vẫn không thể tự sửa thành công, hãy dừng lại, tóm tắt các lỗi gặp phải và xin chỉ thị từ người dùng (Orchestrator).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
