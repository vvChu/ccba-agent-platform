# Ticket 3: [Thiết kế Validation Gate & Metrics Scorer](03-validation-gate-scorer.md)

* **Thuộc bản đồ**: [CCBA Skill Auto-Tuner Map](../map.md)
* **Loại tác vụ**: Research [AFK]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Unblocked)

## 📋 Mục tiêu
Xây dựng bộ chấm điểm (Metrics Scorer) và Cổng kiểm chứng (Validation Gate) đối soát trajectory của Agent với Real Benchmark Logs để chống **Prompt Drift**.

## 🔍 Chi tiết phân tích
- Lấy tập Real Benchmark Logs từ `.md/knowledge/`.
- Thực thi `SKILL.md` bản đề xuất (bản mới sau bước Edit) trên tập Benchmark.
- So sánh điểm số thu được với bản `SKILL.md` gốc. Chỉ chấp nhận bản mới nếu `Score(New) >= Score(Original)` trên 100% bài test Held-out.

## 📌 Đầu ra mong muốn
Quy trình tính điểm (Scoring Pipeline) và hàm điều kiện Validation Gate.
