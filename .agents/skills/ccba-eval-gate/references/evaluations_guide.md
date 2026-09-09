# ccba-skills-eval — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Hướng dẫn thiết lập bộ kiểm thử benchmark và đánh giá độ chính xác của kỹ năng
> **Mô tả gốc:** Khởi chạy hệ thống kiểm thử tự động (Evaluations) cho các kỹ năng AI trong CCBA Platform.

---

# Lệnh /ccba-skills-eval

Khi nhận được lệnh này từ người dùng, Agent sẽ tự động nạp và thực thi công cụ kiểm định chất lượng (Evaluations) cho các kỹ năng AI.

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Xác định phạm vi kiểm thử
Agent phân tích yêu cầu của người dùng để xác định tham số:
- **Kiểm thử một kỹ năng cụ thể:** Nếu người dùng yêu cầu kiểm tra một kỹ năng (ví dụ: `/ccba-skills-eval ccba-copywriting` hoặc viết gọn `copywriting`), xác lập tham số `--skill ccba-copywriting`.
- **Kiểm thử toàn bộ:** Nếu người dùng chỉ gõ lệnh chung `/ccba-skills-eval`, mặc định chạy cho tất cả kỹ năng bằng cách bỏ trống `--skill` hoặc đặt `--skill all`.
- **Số lần chạy thử:** Mặc định chạy 3 lần thử (`--trials 3`) để đo độ tin cậy. Nếu người dùng cần chạy nhanh để kiểm tra lỗi cú pháp, có thể đặt `--trials 1`.

**Tiêu chí hoàn thành:** Xác định rõ kỹ năng mục tiêu và số lượt thử nghiệm.

### Bước 2: Kích hoạt Core Eval Runner & Harness Engine
Chạy lệnh CLI sau tại thư mục gốc của dự án:
```bash
# Kiểm thử một kỹ năng cụ thể qua ccba_harness Multi-Scorer Engine
python -m ccba_harness.cli eval --skill [tên-skill] --trials 3

# Tự động tối ưu hóa SKILL.md (Skill Auto-Tuner via SkillOpt loop)
python -m ccba_harness.cli eval --skill [tên-skill] --auto-tune --trials 3

# Khai phá lỗi từ transcript log thực chiến và tự động sinh test cases
python scripts/eval/log_eval_miner.py --skill [tên-skill] --auto-inject

# Kiểm thử toàn bộ các kỹ năng AI
python -m ccba_harness.cli eval --trials 3
```

**Tiêu chí hoàn thành:** Lệnh ccba-harness eval được khởi chạy với đầy đủ tham số.

### Bước 3: Đánh giá Đa chiều theo Barem Rubrics & Rào chắn Điểm Liệt
- **Bộ Tiêu chí Định lượng & Rubrics:** Đối chiếu kết quả với Quy chuẩn tại [`.md/knowledge/guidelines/domain_success_criteria_rubrics.md`](../../../.md/knowledge/guidelines/domain_success_criteria_rubrics.md):
  * **Code-Based Assertions (< 1ms):** ExactMatch, RegexMatch, JsonSchemaMatch, LengthBounds.
  * **Model-Based Rubrics (Likert 1–5):** Anthropic Prompt Structure (`<rubric>`, `<answer>`, `<thinking>`, `<score>`).
  * **Rào chắn Điểm Liệt (Hard Floor):** Nếu vi phạm tiêu chí cốt lõi (False Negative PCCC, sai hiệu lực văn bản luật, bịa trích dẫn), bài thi bị đánh rớt ngay lập tức (Score = 0.0%) bất kể các tiêu chí phụ.
- **Chế độ Auto-Tuner (`--auto-tune`):** 
  Core Eval Runner sẽ tự động điều phối chu trình 4 bước (**Rollout -> Reflect -> Edit -> Validate**). LLM Optimizer sẽ đề xuất chỉnh sửa văn bản `SKILL.md` và kiểm chứng qua Cổng **Validation Gate** để loại bỏ hiện tượng **Prompt Drift** trước khi cập nhật.
- **Nếu tất cả các test cases đạt PASS (exit code = 0):** Báo cáo kết quả thành công cho người dùng.
- **Nếu có test case bị FAILED (exit code = 1):**
  1. Đọc chi tiết lỗi so khớp (Regex mismatch hoặc LLM Judge feedback) được in trong output log.
  2. Xác định xem lỗi do mô hình suy giảm hiệu năng (regression), lỗi placeholders, hay lỗi over-triggering.
  3. Thực hiện sửa đổi và bổ sung chỉ thị trực tiếp vào tệp `SKILL.md` của kỹ năng bị lỗi đó để khắc phục (tương tự như cách sửa lỗi over-triggering bằng When to Use / When NOT to Use).
  4. Chạy lại kiểm thử (tối đa lặp lại 3 lần). Nếu sau 3 lần vẫn lỗi, hãy báo cáo cụ thể cho người dùng để nhận chỉ thị.

**Tiêu chí hoàn thành:** Hoàn thành đánh giá rubric, không vi phạm điểm liệt.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
