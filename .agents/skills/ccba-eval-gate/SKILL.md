---
name: ccba-eval-gate
description: Thực hiện kiểm chứng mã nguồn thông qua CI Gates tự động và tự động sửa
  lỗi (Self-Healing Loop).
disable-model-invocation: true
bundle: _software
gpi:
  s: 3.0
  k: 2.0
  a: 2.0
  p: 1.0
user-invocable: true
command: /ccba-eval-gate
triggers:
- eval gate
- kiểm chứng
- sửa lỗi tự động
- self-healing
- check code
- run gate
- ccba-skills-eval
- skills-eval
---

# 🛡️ Kỹ năng: eval-gate (Tự kiểm chứng & Sửa lỗi)

Kỹ năng này bọc script [`scripts/eval/run_harness_evals.py`](../../../scripts/eval/run_harness_evals.py), tích hợp framework [`ccba_harness.evals`](../../../packages/ccba-harness/AGENTS.md) và chịu trách nhiệm bảo vệ codebase khỏi các lỗi cú pháp, kiểu dữ liệu, test cases thất bại, phá vỡ hợp đồng Seam, hoặc tài liệu bị ảo ảnh.

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Chạy kiểm định tự động & Auto-Tuning qua Safe Execution Sandbox
Kích hoạt chạy script điều phối chính ngầm qua Wrapper an toàn với `WaitMsBeforeAsync: 1000`:
```bash
# Kích hoạt CI Gates toàn bộ qua Safe Execution Sandbox Wrapper:
python scripts/eval/run_safe_eval_wrapper.py --cmd "python scripts/eval/run_harness_evals.py" --timeout 90

# KHOANH VÙNG TEST (Scoped Test Execution): Chạy file test cụ thể bằng Wrapper an toàn
python scripts/safe_pytest.py -f scripts/tests/test_wiki_health_linter.py

# Khai phá lỗi từ production log và tự động sinh test cases (Eval Flywheel)
python scripts/eval/log_eval_miner.py --skill [tên-skill] --auto-inject

# Tự động tối ưu hóa SKILL.md với Skill Auto-Tuner (SkillOpt loop)
python .agents/skills/ccba-eval-gate/scripts/eval_runner.py --skill [tên-skill] --auto-tune --max-iterations 3
```
*(Lưu ý: Luôn gọi `run_safe_eval_wrapper.py` với `WaitMsBeforeAsync` $\le 2000$ms để đẩy lệnh xuống Background Task. Wrapper tự động ngắt nếu vượt quá timeout và ghi log cô lập tại `.md/scratch/eval_runs/run_<timestamp>.log`).*
- **Tiêu chí hoàn thành:** Kiểm định được kích hoạt qua wrapper an toàn và tạo log cô lập tại thư mục quy định.

### Bước 2: Đánh giá kết quả & Đọc file Chẩn đoán (`diagnostics.json`)
*   **Nếu exit code = 0 (Tất cả Gate PASS):** Codebase sạch sẽ, file `.md/scratch/eval_runs/diagnostics.json` báo `status = PASS`.
*   **Nếu exit code = 1 (Có Gate FAILED/TIMEOUT):** Đọc trực tiếp tệp chẩn đoán cấu trúc `.md/scratch/eval_runs/diagnostics.json` để lấy nguyên nhân gốc (`error_type`, `failed_gate`, `culprit_file`, `summary_traceback`).
- **Tiêu chí hoàn thành:** Xác định chính xác trạng thái PASS hoặc bóc tách nguyên nhân gốc từ tệp chẩn đoán diagnostics.json.

### Bước 3: Vòng lặp tự chữa lỗi (Self-Healing Loop)
Nếu phát hiện Gate bị thất bại:
1.  Đọc tệp chẩn đoán `.md/scratch/eval_runs/diagnostics.json` vừa được sinh ra. Tránh phỏng đoán, đọc trực tiếp 20-25 dòng traceback cô đọng trong trường `summary_traceback`.
2.  Xác định file (`culprit_file`) và dòng code gây lỗi.
3.  Thực hiện sửa đổi trực tiếp lên file lỗi theo nguyên tắc **KISS** (chỉnh sửa nhỏ nhất để sửa lỗi, không refactor lan man).
4.  Quay lại **Bước 1** để chạy lại kiểm tra qua `run_safe_eval_wrapper.py`.
5.  **Giới hạn (Retry Cap):** Chỉ lặp lại tối đa **3 lần**. Nếu sau 3 lần vẫn không thể tự sửa thành công, hãy dừng lại, tóm tắt các lỗi gặp phải và xin chỉ thị từ người dùng.
- **Tiêu chí hoàn thành:** Lỗi được khắc phục và kiểm định chạy lại thành công (hoặc dừng lại báo cáo sau tối đa 3 lần thử).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/evaluations_guide.md` | Hướng dẫn thiết lập bộ kiểm thử benchmark và đánh giá độ chính xác của kỹ năng |

