# Bản đồ Định hướng: CCBA Skill Auto-Tuner (`skillopt-auto-tuner`)

> **Mô tả**: Bản đồ định hướng chia nhỏ và quản lý tiến trình triển khai tính năng tự động tối ưu hóa tệp `SKILL.md` (kế thừa cơ chế Rollout -> Reflect -> Edit -> Validate từ Microsoft SkillOpt).

---

## 🎯 Điểm đích (Destination)
Tích hợp thành công cờ `--auto-tune` vào workflow `/ccba-skills-eval`, cho phép AI Agent tự động tinh chỉnh văn bản hướng dẫn trong `SKILL.md` thông qua tập bài test kiểm thử Hỗn hợp (Synthetic Rollout + Real Validation Gate) với 100% rào chắn bảo vệ chống Prompt Drift.

---

## 📌 Ghi chú (Notes)
- **Phương pháp**: Phân rã ticket theo tiêu chuẩn Wayfinder, chốt quyết định kỹ thuật trước khi code.
- **Kỹ năng bổ trợ**: `ai-gateway-sdk`, `eval-gate`, `writing-great-skills`, `llm-pipeline-patterns`.
- **Rào chắn bắt buộc**: Mọi bản prompt được sửa đổi bởi Optimizer phải đi qua **Validation Gate** trên Real Benchmark Logs trước khi lưu đè lên `SKILL.md`.

---

## 🟢 Quyết định đã chốt (Decisions so far)

1. [Tập trung xây dựng Skill Auto-Tuner](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0023-skill-auto-tuner-integration-via-skillopt.md#1-ph%E1%BA%A1m-vi-%E1%BB%A9ng-d%E1%BB%A5ng-t%E1%BA%ADp-trung-x%C3%A2y-d%E1%BB%B1ng-ccba-skill-auto-tuner): Tự động hóa việc biên soạn `SKILL.md` mà không can thiệp trọng số LLM (Frozen Weights). *(Ghi nhận tại ADR 0023)*.
2. [Chiến lược Benchmark Hỗn hợp](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0023-skill-auto-tuner-integration-via-skillopt.md#2-chi%E1%BA%BFn-l%C6%B0%E1%BB%A3c-benchmark-h%E1%BB%97n-h%E1%BB%A3p-hybrid-benchmark-strategy): Dùng Synthetic Tasks (sinh tự động qua AI Gateway) cho vòng Rollout và Real Benchmark Logs cho Validation Gate. *(Ghi nhận tại ADR 0023)*.
3. [Giao diện CLI Seam `--auto-tune`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0023-skill-auto-tuner-integration-via-skillopt.md#3-giao-di%E1%BB%87n-%C4%91i%E1%BB%81u-khi%E1%BB%83n-cli-seam-m%E1%BB%9F-r%E1%BB%99ng-ccba-skills-eval-b%E1%BA%B1ng-c%E1%BB%9D--auto-tune): Mở rộng `/ccba-skills-eval` bằng cờ `--auto-tune` thay vì tạo workflow riêng lẻ mới. *(Ghi nhận tại ADR 0023)*.

---

## 🧭 Biên giới Công việc & Tickets (Frontier & Open Tickets)

### 🔹 Ticket 1 [AFK]: [Nghiên cứu Optimizer Prompt Pattern cho SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/tickets/01-optimizer-prompt-pattern.md)
* **Loại tác vụ**: Research [AFK]
* **Mục tiêu**: Thiết kế prompt chuẩn cho Optimizer Model (bước Edit) để chỉ đưa ra các chỉnh sửa văn bản dạng Bounded Edits (sửa/thêm/bớt câu hướng dẫn) mà bảo toàn tuyệt đối phần YAML Frontmatter của `SKILL.md`.
* **Trạng thái**: Open (Unblocked)

### 🔹 Ticket 2 [AFK]: [Thiết kế Synthetic Task Generator via AI Gateway](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/tickets/02-synthetic-task-generator.md)
* **Loại tác vụ**: Research [AFK]
* **Mục tiêu**: Xây dựng thuật toán đọc `SKILL.md` và `CONTEXT.md` để tự động sinh 5-10 kịch bản thử nghiệm edge-case đa dạng làm đầu vào cho giai đoạn Rollout.
* **Trạng thái**: Open (Unblocked)

### 🔹 Ticket 3 [AFK]: [Thiết kế Validation Gate & Metrics Scorer](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/tickets/03-validation-gate-scorer.md)
* **Loại tác vụ**: Research [AFK]
* **Mục tiêu**: Xây dựng bộ chấm điểm (Scorer) đối soát trajectory của Agent với Real Benchmark Logs, thiết lập ngưỡng điểm chấp nhận để tránh Prompt Drift.
* **Trạng thái**: Open (Unblocked)

### 🔹 Ticket 4 [HITL]: [Tích hợp CLI Flag --auto-tune vào ccba-skills-eval](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/skillopt-auto-tuner/tickets/04-cli-seam-integration.md)
* **Loại tác vụ**: Task [HITL]
* **Mục tiêu**: Cập nhật file spec `/ccba-skills-eval` và script điều khiển `eval-gate` để nối liền chu trình 4 bước khi người dùng truyền cờ `--auto-tune`.
* **Phụ thuộc**: Blocked by Ticket 1, 2, 3.

---

## 🌫️ Chưa xác định rõ (Not yet specified)
- **Telemetry & Logging Structure**: Cấu trúc lưu trữ lịch sử các phiên tuning (trajectories, prompt diffs, score progression) tại `.md/scratch/auto_tuner/`.
- **Auto-Rollback Strategy**: Cơ chế khôi phục lại `SKILL.md` phiên bản cũ khi các phiên chạy thực tế sau đó gặp phải lỗi suy thoái ngoài ý muốn.

---

## ⛔ Ngoài phạm vi (Out of scope)
- **Model Fine-Tuning**: Không can thiệp chỉnh sửa trọng số (weights) của LLM.
- **Standalone Workflow**: Không tạo lệnh slash mới ngoài `/ccba-skills-eval`.
- **Unverified Commit**: Không cho phép tự động commit `SKILL.md` chưa qua Validation Gate.
