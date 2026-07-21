# Ticket 1: [Nghiên cứu Optimizer Prompt Pattern cho SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/tickets/01-optimizer-prompt-pattern.md)

* **Thuộc bản đồ**: [CCBA Skill Auto-Tuner Map](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/map.md)
* **Loại tác vụ**: Research [AFK]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Unblocked)

## 📋 Mục tiêu
Xây dựng prompt mẫu chuẩn hóa cho LLM Optimizer (bước Edit trong chu trình SkillOpt). 

## 🔍 Chi tiết phân tích
- LLM Optimizer nhận vào:
  1. File `SKILL.md` hiện tại.
  2. Nhật ký thực thi (Trajectories) từ bước Rollout.
  3. Đánh giá nguyên nhân thất bại từ bước Reflect.
- LLM Optimizer phải xuất ra:
  - Bản thảo `SKILL.md` mới với các chỉnh sửa dạng **Bounded Edits** (chỉ bổ sung rào chắn, làm rõ câu từ, loại bỏ chỉ dẫn mơ hồ).
  - Bắt buộc giữ nguyên vẹn cấu trúc YAML Frontmatter (`name`, `description`, `triggers`, `applies_to`, `bundle`) để không làm hỏng trình parse `catalog.yaml`.

## 📌 Đầu ra mong muốn
Tệp Markdown chứa mẫu prompt hệ thống dành cho Optimizer Model và bộ quy tắc kiểm định cấu trúc (Frontmatter Integrity Gate).
