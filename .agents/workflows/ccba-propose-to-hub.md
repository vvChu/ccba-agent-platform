---
description: Đề xuất tích hợp skill/workflow/tool hoặc rules/directory mới từ Spoke lên Hub
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
disable-model-invocation: true
---
# Workflow: Propose to Hub (Đóng Góp Ngược Lên Hub)

Quy trình chuẩn hóa đề xuất đóng góp ngược các cải tiến từ dự án Spoke lên Platform Hub chung.

## Bước 1: Thu thập thông tin đề xuất
Hỏi người dùng tuần tự từng câu hỏi sau để ghi nhận đề xuất:
1. **Loại đề xuất:** `skill` / `workflow` / `tool` / `rules`.
2. **Tên đề xuất:** Dạng kebab-case (ví dụ: `auto-pdf-namer`).
3. **Mô tả:** Giải thích ngắn gọn mục đích (1-2 câu).
4. **Vấn đề giải quyết:** Chi tiết khó khăn thực tế cần giải quyết.
5. **Dự án áp dụng:** Các bộ môn áp dụng cụ thể.
6. **Mức độ ưu tiên:** "Cao" / "Trung bình" / "Thấp".

## Bước 2: Kiểm tra trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent bắt buộc phải kiểm tra hệ thống để tránh trùng lặp:
1. Đọc tệp cấu hình `.md/workspace_context.yaml` để lấy đường dẫn Hub (`hub_path`).
2. Đọc tệp catalog của Hub tại `<hub_path>/.agents/skills/platform-loader/catalog.yaml` để tìm kiếm tên hoặc mô tả tương tự.
3. Đọc tệp hiến pháp `<hub_path>/.agents/AGENTS.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Báo cáo cho người dùng và đề xuất cập nhật/nâng cấp thành phần cũ thay vì tạo mới.

## Bước 3: Tạo và Commit Đề xuất trên Branch mới
Thực thi các lệnh Git tại thư mục Hub (`hub_path`):
1. **Kiểm tra trạng thái workspace:**
   Chạy `git status`. Nếu có thay đổi chưa commit, yêu cầu người dùng commit hoặc stash các thay đổi đó trước khi tiếp tục.
2. **Đồng bộ main:**
   ```bash
   git checkout main && git pull origin main
   ```
3. **Tạo branch và ghi nhận proposal:**
   - Tạo branch mới: `git checkout -b proposal/[tên-đề-xuất]`
   - Tạo tệp proposal tại: `<hub_path>/.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md`
   
   *Cấu trúc tệp proposal:*
   ```markdown
   ---
   proposal_id: "[YYYY-MM-DD]_[tên-đề-xuất]"
   type: "[loại-đề-xuất]"
   name: "[tên-đề-xuất]"
   status: "open"
   priority: "[mức-độ-ưu-tiên]"
   proposed_by_project: "[tên-dự-án-spoke]"
   proposed_date: "[YYYY-MM-DD]"
   applies_to:
     - "[bộ-môn-áp-dụng]"
   ---
   
   ## Mô tả
   ...
   ## Vấn đề giải quyết
   ...
   ## Giải pháp / Cấu trúc đề xuất
   ...
   ```
4. **Commit & Push:**
   Thực hiện commit và push lên remote branch (do thư mục `.agents/proposals/` đã được whitelist trong `.gitignore`, bạn có thể dùng lệnh add thông thường):
   ```bash
   git add .agents/proposals/ && git commit -m "docs(proposal): add proposal for [tên-đề-xuất]" && git push origin proposal/[tên-đề-xuất]
   ```

## Bước 4: Tạo Pull Request (PR Flow)
Kiểm tra quyền qua GitHub CLI bằng cách chạy `gh auth status` hoặc kiểm tra biến môi trường:
- **Nếu có quyền:** Chạy lệnh tạo PR:
  ```bash
  gh pr create --title "docs(proposal): add proposal for [tên-đề-xuất]" --body "Automated proposal submission." --base main --head proposal/[tên-đề-xuất]
  ```
- **Nếu không có quyền:** Cung cấp link tạo PR thủ công dựa trên remote URL lấy được từ `git remote get-url origin`:
  👉 `[PR-creation-URL]/pull/new/proposal/[tên-đề-xuất]`

## Bước 5: Báo cáo hoàn tất
Báo cáo ngắn gọn cho người dùng bao gồm: đường dẫn tệp đề xuất, tên branch, URL của Pull Request (hoặc link tạo thủ công) và bước tiếp theo.
