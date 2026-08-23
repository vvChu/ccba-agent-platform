# Bản đồ Định hướng (Wayfinder Map): Tối ưu hóa CCBA Setup & Phỏng vấn Tương tác

> **Mã số Feature**: `ccba-platform-setup-optimizations`  
> **Trạng thái**: Đã lập bản đồ (Frontier Open)

---

## 🎯 1. Điểm đích (Destination)

Nâng cấp kỹ năng [`/ccba-setup-skills`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-setup-skills/SKILL.md) và các quy trình phỏng vấn tương tác trên **CCBA Agent Platform** nhằm:
- Giảm tối đa các câu hỏi thừa thông qua trinh sát điều kiện trước (Smart Skipping).
- Tự động suy luận cấu trúc Monorepo để chốt Single/Multi-context mà không cần phỏng vấn thủ công.
- Chuẩn hóa ngôn ngữ phỏng vấn theo mẫu **Recommended-First UX**.
- Duy trì 100% tính độc lập và sở hữu tri thức cục bộ tại Spoke (`.md/knowledge/`).

---

## 📝 2. Ghi chú (Notes)

- Các kỹ năng liên quan: [`ccba-setup-skills`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-setup-skills/SKILL.md), [`grilling`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/grilling/SKILL.md), [`domain-modeling`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/domain-modeling/SKILL.md).
- Quy chuẩn lưu trữ: Tất cả file cấu hình Spoke tiếp tục duy trì tại `.md/knowledge/agents/` và `.md/workspace_context.yaml`.

---

## 🗺️ 3. Frontier Tickets (Các ticket tại Biên giới)

### 🎫 [Ticket #01: Tự động bỏ câu hỏi Triage khi thiếu Skill Triage](01-smart-skipping-triage.md)
- **Loại**: `Research [AFK]`
- **Mục tiêu**: Bổ sung bước trinh sát kiểm tra sự tồn tại của skill `triage` trong `catalog.yaml` / `.agents/skills/`. Nếu không có, tự động bỏ qua phỏng vấn Triage labels.
- **Trạng thái**: CLOSED (Đã nghiên cứu tại [research_01_smart_skipping.md](research_01_smart_skipping.md))

### 🎫 [Ticket #02: Tự động suy luận Monorepo để chốt Single/Multi-Context](02-monorepo-inference.md)
- **Loại**: `Task [AFK]`
- **Mục tiêu**: Bổ sung thuật toán quét các file đặc trưng Monorepo (`pnpm-workspace.yaml`, `workspaces` trong `package.json`, `CONTEXT-MAP.md`). Nếu không thấy tín hiệu Monorepo ➔ Tự động chốt `single-context` mà không làm phiền người dùng.
- **Trạng thái**: CLOSED (Đã triển khai trong `ccba-setup-skills/SKILL.md`)

### 🎫 [Ticket #03: Chuẩn hóa Recommended-First UX cho toàn bộ Phỏng vấn](03-recommended-first-ux.md)
- **Loại**: `Task [AFK]`
- **Mục tiêu**: Đánh giá và cập nhật lại câu từ phỏng vấn trong `ccba-setup-skills` và `ccba-platform` để luôn đưa Lựa chọn 1 (Recommended) lên dòng đầu tiên.
- **Trạng thái**: CLOSED (Đã triển khai trong `ccba-setup-skills/SKILL.md`)

---

## 🌫️ 4. Sương mù chiến trận (Not yet specified)

- **Cơ chế tương thích ngược (Backward Compatibility)**: Chưa xác định rõ cách xử lý khi một Spoke cũ chạy lại lệnh setup — có nên ghi đè hoàn toàn `workspace_context.yaml` hay chỉ hợp nhất (merge) các trường còn thiếu?
- **Đồng bộ Hub ➔ Spoke Auto-Migration**: Cách thông báo cho các dự án Spoke cập nhật logic setup mới qua `/ccba-update-spoke`.

---

## 🚫 5. Ngoài phạm vi (Out of scope)

- Thay đổi vị trí lưu trữ tri thức `.md/knowledge/` sang `docs/` chuẩn MattPocock (CCBA giữ nguyên kiến trúc `.md/knowledge/`).
- Bắt buộc người dùng chuyển sang sử dụng GitHub Issues nếu họ đang dùng Local Markdown.

---

## ✅ 6. Quyết định đã chốt (Decisions so far)

- **ADR-010**: Học hỏi 4 tư duy thiết kế setup từ `mattpocock/skills` để tối ưu trải nghiệm khởi tạo cấu hình trên CCBA Platform.
- **Quyết định Ticket #01**: Áp dụng thuật toán trinh sát **Multi-tier Detection 3 cấp** (Local folder ➔ Catalog registry ➔ Available Skills prompt context). Nếu không tìm thấy skill `triage` ➔ Tự động bỏ qua phỏng vấn Triage labels và cập nhật linh hoạt template `issue-tracker-local.md` để tránh broken link. (Xem chi tiết tại [research_01_smart_skipping.md](research_01_smart_skipping.md)).
- **Quyết định Ticket #02 & #03**: Đã hoàn tất cài đặt Monorepo Inference và Recommended-First UX vào `.agents/skills/ccba-setup-skills/SKILL.md`. Tự động giảm từ 3 câu hỏi phỏng vấn xuống 1 câu hỏi duy nhất cho các dự án Spoke đơn giản.
