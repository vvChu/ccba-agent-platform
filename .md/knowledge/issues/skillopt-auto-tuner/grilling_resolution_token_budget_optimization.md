# 🏛️ CCBA Grilling Resolution: Nightly Tuner Token Budget & Efficiency Architecture

> **Thời gian:** `2026-09-21 05:45:00`  
> **Chủ đề:** Tối ưu hóa Ngân sách Token & Hiệu suất Vận hành Nightly Auto-Tuner Daemon  
> **Tham chiếu:** ADR-0023, ADR-0043, ADR-0052, ADR-0058  
> **Phương pháp:** Socrates Grilling Loop (Nhánh A: Stress-Test Thiết kế)

---

## 1. Bối Cảnh & Đề Xuất Ban Đầu
* **Đề xuất ban đầu của Người dùng:** Nâng trần ngân sách Token hàng đêm từ `5,000,000` lên `> 20,000,000` tokens để tăng tốc tối ưu toàn bộ catalog 74 kỹ năng.
* **Dữ liệu thực nghiệm phiên chạy 2026-09-21 00:00:**
  * Tổng token tiêu thụ: `5,001,119 tokens` qua 19 skills trong ~4 giờ.
  * Chỉ có 1 kỹ năng cải thiện thành công (`ccba-implement`, +8.0%, ngốn 77,980 tokens).
  * 11 kỹ năng dính plateau ngốn tới **~4,600,000 tokens (92% tổng budget)** với $\Delta = 0\%$.

---

## 2. Cây Quyết Định & Các Quyết Định Đã Chốt (Consensus Decisions)

### Quyết định 1: Giữ Khung Giờ Ban Đêm & Không Tăng Ngân Sách Toàn Cục Thô Bạo
* **Vấn đề:** 20M tokens sẽ kéo dài thời gian chạy từ 4 giờ lên 12–15 giờ, tràn sâu vào giờ hành chính (business hours), cạnh tranh tài nguyên GPU và rate-limit LiteLLM Gateway (:8090) trên Server Spark.
* **Quyết định chốt:** 
  * Giữ nguyên cửa sổ chạy đêm 6 tiếng (`00:00 – 06:00`).
  * Duy trì trần tổng phiên đêm ở mức **6,000,000 – 8,000,000 tokens**.

### Quyết định 2: Thiết Lập Trần Token Đơn Kỹ Năng (Per-Skill Budget Ceiling)
* **Vấn đề:** Các kỹ năng dính plateau chạy hết `patience = 3` ngốn từ 300k đến 650k tokens/skill nhưng 100% bị rollback.
* **Quyết định chốt:**
  * Áp trần cứng **150,000 – 200,000 tokens / kỹ năng** khi $\Delta = 0\%$.
  * Nếu vượt ngưỡng này mà chưa sinh ra commit hợp lệ nào $\rightarrow$ Kích hoạt `HALT_PER_SKILL_BUDGET` dừng sớm ngay lập tức.
  * *Lợi ích lượng hóa:* Tiết kiệm ngay **~3.5M tokens/đêm**, cho phép mở rộng số kỹ năng được quét lên 35–40 skills trong cùng ngân sách.

### Quyết định 3: Cơ Chế Cooldown Penalty & Bảo Toàn Escalation Briefs
* **Vấn đề:** Hàng đợi `WeightedPriorityQueue` ưu tiên các kỹ năng điểm thấp (< 90%). Do đó các kỹ năng vừa dính plateau đêm nay sẽ tiếp tục bị đưa lên đầu hàng đợi vào đêm mai, tạo ra vòng lặp đốt token vô tận (*Infinite Plateau Burn Loop*). Đồng thời, script dọn dẹp worktree hiện tại bỏ quên thư mục `.md/knowledge/escalations/`.
* **Quyết định chốt:**
  * **Cooldown Penalty (3–5 ngày):** Kỹ năng dính plateau sẽ được gán nhãn hạ ưu tiên trong hàng đợi trong 3–5 ngày để nhường lượt cho các kỹ năng mới.
  * **Bảo toàn Escalation:** Cập nhật hàm `cleanup_worktree()` trong `run_nightly_tuner.sh` để sao lưu tự động `.md/knowledge/escalations/` về Project Root, phục vụ kỹ sư rà soát ban ngày bằng `/boost` hoặc mô hình suy luận cao cấp (`gemini-3.8-flash-high` / `pro`).

---

## 3. Lộ Trình Triển Khai Kỹ Thuật (Action Plan)

1. **`packages/ccba-harness/src/ccba_harness/evals/tuner.py` & `daemon.py`:**
   - Thêm tham số cấu hình `per_skill_token_budget = 200_000`.
   - Bổ sung logic kiểm tra ngắt sớm `HALT_PER_SKILL_BUDGET` trong vòng lặp Git-Ratchet.
   - Thêm logic Cooldown cho `WeightedPriorityQueue` dựa trên kết quả các báo cáo gần nhất trong `.md/knowledge/reports/`.
2. **`scripts/cron/run_nightly_tuner.sh`:**
   - Điều chỉnh default token-budget lên `6,000,000` hoặc `8,000,000`.
   - Bổ sung dòng sao lưu thư mục `.md/knowledge/escalations/` trước khi dọn dẹp worktree.
3. **Kiểm thử tự động:**
   - Bổ sung unit tests trong `packages/ccba-harness/tests/test_tuner_daemon.py` kiểm chứng:
     - Ngắt sớm khi chạm `per_skill_token_budget`.
     - Thứ tự ưu tiên giảm dần cho các skill đang trong thời gian Cooldown.
