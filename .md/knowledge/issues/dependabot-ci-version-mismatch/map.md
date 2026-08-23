# Wayfinder Navigation Map: Khai Thác Nguyên Nhân & Xử Lý Dứt Điểm Dependabot PRs Bị Lỗi CI

**Mã vấn đề**: `issue-dependabot-ci-version-mismatch`  
**Trạng thái bản đồ**: 🟢 **Đã hoàn thành 100%** — Đã đóng PRs rác và nạp rào chắn ignore trong dependabot.yml  
**Khởi tạo**: 2026-07-24  

---

## 🎯 1. Điểm đích (Destination)
1. **Phân tích nguyên nhân gốc rễ (Root Cause Analysis)**: Xác định chính xác tại sao Dependabot liên tục khởi tạo các PRs nâng cấp `actions/checkout` và `actions/setup-python` lên phiên bản `v7` gây ra hỏng toàn bộ 6/6 CI checks.
2. **Dọn dẹp PRs bị lỗi (Clean obsolete PRs)**: Đóng (Close) 2 PRs #169 và #170 đang bị lỗi CI trên GitHub.
3. **Phòng ngừa tái diễn (Dependabot Pinning & Ignore Guardrail)**: Cấu hình bổ sung rào chắn `ignore` quy tắc `semver-major` nâng cấp tự động đối với các GitHub Actions chính trong file `.github/dependabot.yml` để ngăn Dependabot tự ý tạo PRs phá vỡ phiên bản ổn định.

---

## 📝 2. Ghi chú (Notes)
- Phiên bản ổn định hiện tại của repository đã được cố định tại PR #178: `actions/checkout@v4` và `actions/setup-python@v5`.
- Tùy chọn `ignore` với `update-types: ["version-update:semver-major"]` trong `dependabot.yml` giúp ngăn chặn việc nâng cấp phiên bản major khi chưa được kiểm chứng tại local.

---

## ✅ 3. Quyết định đã chốt (Decisions so far)
- [Phát hiện nguyên nhân Dependabot](../../../../.github/dependabot.yml#L20-L26): Dependabot được cấu hình quét `package-ecosystem: "github-actions"` hàng tuần mà chưa có rào chắn `ignore semver-major`.
- [Cố định phiên bản CI ổn định](../../../../.github/workflows/ci.yml#L21): Nhánh `main` đã chuẩn hóa sử dụng `actions/checkout@v4` và `actions/setup-python@v5`.

---

## 🚀 4. Vé Biên giới & Lộ trình Thực thi (Frontier Tickets)

- 🟢 [Ticket 1: Close 2 PRs Dependabot bị hỏng CI (#169 và #170)](tickets.md#ticket-dependabot-1) `Task [AFK]` — Chạy `gh pr close` để dọn dẹp PRs rác.
- 🟢 [Ticket 2: Cấu hình Ignore Guardrail trong dependabot.yml](tickets.md#ticket-dependabot-2) `Task [AFK]` — Bổ sung `ignore` semver-major cho `actions/checkout` và `actions/setup-python`.
- 🟡 [Ticket 3: Đẩy commit & Kiểm tra tính ổn định của CI](tickets.md#ticket-dependabot-3) `Task [AFK]` — Đẩy `dependabot.yml` lên `main` và kiểm tra `validate_docs.py`.

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- Tự động hóa Dependabot PR Auto-Merge cho các patch minor security updates thông qua GitHub Actions.

---

## ⛔ 6. Ngoài phạm vi (Out of scope)
- Tắt hoàn toàn dịch vụ Dependabot trên kho lưu trữ.
