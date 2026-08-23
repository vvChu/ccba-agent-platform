---
description: Khởi chạy vòng lặp tối ưu hóa kỹ năng AI tự động qua đêm (Git-Ratchet
  Auto-Tuner) lấy cảm hứng từ karpathy/autoresearch.
disable-model-invocation: true
bundle: _core
command: /ccba-autoresearch
triggers:
- autoresearch
- auto-research
- git ratchet
- ratchet
- auto tune
- auto-tune
- tối ưu qua đêm
- tối ưu prompt tự động
---
# Lệnh /ccba-autoresearch

Khi nhận được lệnh này từ người dùng, Agent sẽ tự động nạp và thực thi công cụ tối ưu hóa tự động **Git-Ratchet Auto-Tuner** (`scripts/eval/git_ratchet_tuner.py`).

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Kiểm tra hoặc Tạo tệp `program.md`
Agent kiểm tra xem thư mục gốc đã có tệp `program.md` chưa:
- Nếu chưa có, copy mẫu từ [`.agents/skills/eval-gate/program_template.md`](../skills/eval-gate/program_template.md) vào `program.md` và điều chỉnh `Target File` theo yêu cầu của người dùng.

### Bước 2: Kích hoạt Git-Ratchet Auto-Tuner
Chạy lệnh CLI sau tại thư mục gốc của dự án:
```bash
# Chạy tối ưu hóa theo đặc tả trong program.md (có Git commit tự động)
python scripts/eval/git_ratchet_tuner.py --program program.md

# Chạy thử nghiệm an toàn không commit git (Dry-run mode)
python scripts/eval/git_ratchet_tuner.py --program program.md --dry-run-git

# Chạy tối ưu một kỹ năng trực tiếp qua CLI
python scripts/eval/git_ratchet_tuner.py --target .agents/skills/copywriting/SKILL.md --max-trials 10 --target-score 90.0
```

### Bước 3: Đánh giá Báo cáo Ratchet
- Đọc bảng tổng kết:
  * Điểm số cải thiện: `Start Score` $\rightarrow$ `Final Score`.
  * Số commits thành công được lưu lại (`kept_commits`).
  * Số lần tự động rollback khi không đạt điểm (`reverted_trials`).
- Báo cáo kết quả rõ ràng và hiển thị `git log` tóm tắt các cải tiến đã đạt được.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
