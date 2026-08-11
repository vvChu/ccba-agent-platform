# Báo cáo Nghiên cứu: Đồng bộ Chuỗi Onboarding /ccba-platform → /ccba-init-spoke → /ccba-setup-skills

- **Mã số**: `research-platform-init-setup-sync`
- **Dự án**: `CCBA Agent Platform`
- **Loại tài liệu**: Technical Research Report (Double-Pass Adversarial Review)
- **Các kỹ năng đối soát**: `ccba-platform` (v3.2), `ccba-init-spoke`, `ccba-setup-skills`

---

## 1. Tóm tắt Thực thi (Executive Summary)

Chuỗi kỹ năng onboarding hiện tại của hệ thống CCBA Hub-and-Spoke đã hình thành khung xương vững chắc nhưng vẫn tồn tại sự giẫm chân (overlap) và xung đột luồng xử lý giữa các kỹ năng. Cụ thể, kỹ năng toàn cục `ccba-platform` (Global) đang gánh vác quá nhiều logic phỏng vấn khởi tạo cục bộ ở Bước 3 (Interactive Setup) thay vì ủy quyền (delegate) cho kỹ năng phát triển phần mềm chuyên biệt `ccba-setup-skills`. Việc này gây ra rào cản cản trở thao tác nhanh (Lazy Setup).

Báo cáo đề xuất tái cấu trúc lại luồng onboarding thành chuỗi thống nhất: **`/ccba-platform` (Cổng điều phối Router) ➔ `/ccba-init-spoke` (Tạo cấu trúc Spoke) ➔ `/ccba-setup-skills` (Cấu hình Công cụ Dev)**, đảm bảo tôn trọng nguyên tắc Single Source of Truth cho `workspace_context.yaml` và triết lý Lazy Setup của `mattpocock/skills`.

---

## 2. Kết quả Nghiên cứu Chi tiết (Key Findings)

### 2.1. Phân tích Hành trình Onboarding (User Journey)
- **Hiện trạng**:
  1. Người dùng gọi `/ccba-platform` ➔ Bước 3 (Interactive Setup) trong `ccba-platform` kiểm tra `workspace_context.yaml`, nếu thấy thiếu trường `issue_tracker` hoặc `triage_disciplines` thì lập tức dừng lại hỏi phỏng vấn tương tác 2 câu hỏi.
  2. Người dùng sau đó chọn `1` (`init spoke`) để tạo dự án mới.
  3. Người dùng tiếp tục chạy `/ccba-setup-skills` và bị phỏng vấn lại về `issue_tracker`.
- **Đánh giá**: Luồng này bị lặp trùng câu hỏi và phá vỡ triết lý Lazy Setup. `/ccba-platform` bị gán nhầm vai trò của một Setup Wizard.

### 2.2. Điểm Mẫu Thuẫn Schema Dữ Liệu (Schema Alignment)
- **`workspace_context.yaml`**:
  - `/ccba-init-spoke` khởi tạo với `project.name`, `project.type`, `project.mode`, `project.qc_mode`. Nó chưa thiết lập trường `project.issue_tracker`.
  - `/ccba-platform` kiểm tra `issue_tracker` ở dạng không nhất quán.
  - `/ccba-setup-skills` lại ghi nhận chuẩn xác vào `project.issue_tracker` và sinh bộ chỉ dẫn tại `.md/knowledge/agents/issue_tracker.md`.
- **Phân định Trách nhiệm**:
  - `/ccba-init-spoke`: Chịu trách nhiệm tạo thư mục `.md/` và khởi tạo khung `workspace_context.yaml`.
  - `/ccba-setup-skills`: Chịu trách nhiệm duy nhất cho việc phỏng vấn `issue_tracker`, tạo `.md/knowledge/agents/` và ghi khối `## Agent skills` vào `AGENTS.md`.

### 2.3. Đối chiếu với Bài học từ `mattpocock/skills`
- **Lazy Setup**: `mattpocock/skills` chỉ phỏng vấn cấu hình khi người dùng chủ động chạy kỹ năng setup kỹ thuật. Việc `/ccba-platform` chặn người dùng ở Global Menu là vi phạm Lazy Setup.
- **Smart Skipping & Monorepo Inference**: `/ccba-setup-skills` đã triển khai thành công logic này (bỏ qua Triage khi không có skill, tự chốt Single-context khi không có Monorepo), cần được kế thừa nhất quán trên toàn hệ thống.

---

## 3. Khuyến nghị Triển khai (Implementation Recommendations)

1. **Tinh gọn `/ccba-platform` về đúng vai trò Global Router (Chỉ làm Liveness Check & Menu)**:
   - Loại bỏ hoàn toàn Bước 3 (Interactive Setup) khỏi `C:\Users\chuvu\.gemini\config\skills\ccba-platform\SKILL.md`.
   - Giữ `/ccba-platform` tập trung 100% vào việc: (a) Kiểm tra VPN Gateway `:8090`, (b) Kiểm tra thư mục `.md/` có tồn tại không (nếu chưa có ➔ Đề xuất chạy ngay `/ccba-init-spoke`), (c) Hiển thị Menu 14 lựa chọn siêu tốc.

2. **Gắn kết Chuỗi Workflow (Chain Workflow)**:
   - Cập nhật `/ccba-init-spoke.md` ở Bước 8 (Báo cáo hoàn tất) để tự động nhắc nhở người dùng bước kế tiếp: *"Dự án đã được khởi tạo. Tiếp theo, hãy gõ `/ccba-setup-skills` để thiết lập công cụ phát triển phần mềm (Issue Tracker/Domain Docs)."*

3. **Chuẩn hóa 100% Schema `project.issue_tracker`**:
   - Tất cả các skill đọc/ghi duy nhất trường `project.issue_tracker` trong `.md/workspace_context.yaml`.

---

## 4. Tài liệu Tham chiếu & Citations (References & Citations)

- `C:\Users\chuvu\.gemini\config\skills\ccba-platform\SKILL.md` (Dòng 34-40: Bước Interactive Setup trùng lặp).
- `d:\GitHubProjects\ccba-agent-platform\.agents\workflows\ccba-init-spoke.md` (Dòng 34-60: Khởi tạo schema `workspace_context.yaml`).
- `d:\GitHubProjects\ccba-agent-platform\.agents\skills\ccba-setup-skills\SKILL.md` (Pha 1 & Pha 2: Smart Skipping & Recommended-First UX).

---

## 5. Quyết định đã làm rõ qua Grill-with-Docs (Resolved Decisions — ADR-011)

- **Q1 (Luồng Chaining khi Init Spoke)**: Đã chốt theo triết lý *Lazy Setup*. Ở bước cuối của `/ccba-init-spoke`, in thông báo gợi ý rõ ràng và chờ người dùng gõ `/ccba-setup-skills` khi họ sẵn sàng (không tự động gọi ngầm để đảm bảo quyền chủ động cho người dùng).
- **Q2 (Xử lý Cấu hình cũ khi Switch Tracker)**: Áp dụng cơ chế *Idempotent Overwrite with Backup*. Khi chuyển đổi Issue Tracker qua `/ccba-setup-skills`, hệ thống ghi đè file cấu hình mới và tự động đổi tên file cũ thành `issue_tracker.md.bak` nếu có dữ liệu task cũ để chống mất mát dữ liệu.
