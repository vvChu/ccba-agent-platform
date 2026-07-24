# Danh sách Ticket Chi Tiết: Xử Lý Dependabot PRs Lỗi CI & Cấu Hình Rào Chắn

**Mã bản đồ**: `issue-dependabot-ci-version-mismatch`  
**Đường dẫn bản đồ**: [map.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/dependabot-ci-version-mismatch/map.md)  

---

## 🟢 Ticket 1: Close 2 PRs Dependabot bị hỏng CI (#169 và #170)

- **Mã Ticket**: `ticket-dependabot-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**:
  - Chạy `gh pr close 169` và `gh pr close 170` để đóng các PRs lỗi do Dependabot tạo nâng cấp major version không tương thích.

---

## 🟢 Ticket 2: Cấu hình Ignore Guardrail trong `dependabot.yml`

- **Mã Ticket**: `ticket-dependabot-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Tệp tin tác động**: `[MODIFY] .github/dependabot.yml`
- **Mục tiêu**:
  - Bổ sung cấu hình `ignore` với `update-types: ["version-update:semver-major"]` cho phần `package-ecosystem: "github-actions"`.
  - Ngăn ngừa Dependabot tự ý tạo PRs nâng cấp major version phá vỡ tính tương thích CI.

---

## 🟡 Ticket 3: Đẩy commit & Kiểm tra tính ổn định của CI

- **Mã Ticket**: `ticket-dependabot-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by `ticket-dependabot-1`, `ticket-dependabot-2`
- **Tệp tin tác động**: `.github/dependabot.yml`
- **Mục tiêu**:
  - Đẩy thay đổi `dependabot.yml` lên nhánh `main`.
  - Kiểm tra `validate_docs.py` đạt 100% PASS.
