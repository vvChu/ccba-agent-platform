---
name: eval-gate
description: Thực hiện kiểm chứng mã nguồn thông qua CI Gates tự động và tự động sửa lỗi (Self-Healing Loop).
---

# 🛡️ Kỹ năng: eval-gate (Tự kiểm chứng & Sửa lỗi)

Kỹ năng này bọc script `scripts/run_harness_evals.py` và chịu trách nhiệm bảo vệ codebase khỏi các lỗi cú pháp, kiểu dữ liệu, test cases thất bại hoặc tài liệu bị ảo ảnh.

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Chạy kiểm định tự động & Auto-Tuning qua Safe Execution Sandbox
Kích hoạt chạy script điều phối chính ngầm qua Wrapper an toàn với `WaitMsBeforeAsync: 1000`:
```bash
# Kích hoạt CI Gates toàn bộ qua Safe Execution Sandbox Wrapper:
.venv\Scripts\python.exe scripts/run_safe_eval_wrapper.py --cmd ".venv\Scripts\python.exe scripts/run_harness_evals.py" --timeout 90

# KHOANH VÙNG TEST (Scoped Test Execution): Chạy file test cụ thể để tiết kiệm thời gian
.venv\Scripts\pytest -q tests/test_agent_execution_guardrails.py

# Tự động tối ưu hóa SKILL.md với Skill Auto-Tuner (SkillOpt loop)
python .agents/skills/eval-gate/scripts/eval_runner.py --skill [tên-skill] --auto-tune --max-iterations 3
```
*(Lưu ý: Luôn gọi `run_safe_eval_wrapper.py` với `WaitMsBeforeAsync` $\le 2000$ms để đẩy lệnh xuống Background Task. Wrapper tự động ngắt nếu vượt quá timeout và ghi log cô lập tại `.md/scratch/eval_runs/run_<timestamp>.log`).*

### Bước 2: Đánh giá kết quả & Đọc file Chẩn đoán (`diagnostics.json`)
*   **Nếu exit code = 0 (Tất cả Gate PASS):** Codebase sạch sẽ, file `.md/scratch/eval_runs/diagnostics.json` báo `status = PASS`.
*   **Nếu exit code = 1 (Có Gate FAILED/TIMEOUT):** Đọc trực tiếp tệp chẩn đoán cấu trúc `.md/scratch/eval_runs/diagnostics.json` để lấy nguyên nhân gốc (`error_type`, `failed_gate`, `culprit_file`, `summary_traceback`).

### Bước 3: Vòng lặp tự chữa lỗi (Self-Healing Loop)
Nếu phát hiện Gate bị thất bại:
1.  Đọc tệp chẩn đoán `.md/scratch/eval_runs/diagnostics.json` vừa được sinh ra. Tránh phỏng đoán, đọc trực tiếp 20-25 dòng traceback cô đọng trong trường `summary_traceback`.
2.  Xác định file (`culprit_file`) và dòng code gây lỗi.
3.  Thực hiện sửa đổi trực tiếp lên file lỗi theo nguyên tắc **KISS** (chỉnh sửa nhỏ nhất để sửa lỗi, không refactor lan man).
4.  Quay lại **Bước 1** để chạy lại kiểm tra qua `run_safe_eval_wrapper.py`.
5.  **Giới hạn (Retry Cap):** Chỉ lặp lại tối đa **3 lần**. Nếu sau 3 lần vẫn không thể tự sửa thành công, hãy dừng lại, tóm tắt các lỗi gặp phải và xin chỉ thị từ người dùng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
