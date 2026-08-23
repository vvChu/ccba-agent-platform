# Ticket 2: [Thiết kế Synthetic Task Generator via AI Gateway](02-synthetic-task-generator.md)

* **Thuộc bản đồ**: [CCBA Skill Auto-Tuner Map](../map.md)
* **Loại tác vụ**: Research [AFK]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Unblocked)

## 📋 Mục tiêu
Nghiên cứu cơ chế tự động sinh ra tập các bài thử nghiệm giả lập (Synthetic Tasks) để sử dụng cho giai đoạn **Rollout**.

## 🔍 Chi tiết phân tích
- Đọc nội dung `SKILL.md` và các thuật ngữ từ `CONTEXT.md`.
- Sử dụng `ccba-ai` (AI Gateway) để sinh ra 5-10 kịch bản câu hỏi/bài tập đa dạng bao gồm cả các tình huống biên (edge-cases) phức tạp.
- Đảm bảo mỗi task bao gồm: Input Prompt, Expected Constraints, và Acceptance Rubric.

## 📌 Đầu ra mong muốn
Thuật toán/script sinh Synthetic Tasks và định dạng JSON Schema lưu trữ danh sách tasks.
