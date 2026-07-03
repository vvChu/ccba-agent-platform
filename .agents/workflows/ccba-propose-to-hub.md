---
description: Đề xuất tích hợp skill/workflow/tool hoặc rules/directory mới từ Spoke lên Hub
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
---

# Workflow: Propose to Hub (Đóng Góp Ngược Lên Hub)

Gọi lệnh: `/ccba-propose-to-hub`

---

## Bước 1: Thu thập thông tin đề xuất

Hỏi người dùng tuần tự các câu hỏi sau để điền vào đề xuất:
1. **Loại đề xuất:** `skill` / `workflow` / `tool` / `rules/directory`.
2. **Tên đề xuất:** Tên ngắn gọn dạng kebab-case (ví dụ: `auto-pdf-namer`).
3. **Mô tả:** 1-2 câu giải thích mục đích.
4. **Vấn đề giải quyết:** Chi tiết khó khăn thực tế cần giải quyết.
5. **Dự án áp dụng:** Bộ môn cụ thể hoặc `Tất cả`.
6. **Code mẫu / Cấu trúc thư mục mẫu:** (Nếu có).
7. **Mức độ ưu tiên:** `Cao` / `Trung bình` / `Thấp`.

---

## Bước 2: Kiểm tra trùng lặp (Duplicate Detection)

Trước khi tạo mới, Agent bắt buộc phải kiểm tra hệ thống để tránh trùng lặp:
1. Đọc tệp cấu hình `.agents/workspace_context.yaml` để lấy `hub_path`.
2. Đọc tệp catalog của Hub tại `<hub_path>/.agents/skills/platform-loader/catalog.yaml` để tìm kiếm tên hoặc mô tả tương tự.
3. Đọc tệp hiến pháp `<hub_path>/.agents/AGENTS.md`.
*Nếu phát hiện đã trùng lặp:* Báo cáo cho người dùng và đề xuất cập nhật/nâng cấp thành phần cũ thay vì tạo mới.

---

## Bước 3: Tạo và Commit Đề xuất trên Branch mới

Thực thi các lệnh Git tại thư mục `<hub_path>`:
1. **Kiểm tra trạng thái workspace:**
   * Chạy `git status`. Nếu có thay đổi chưa commit, yêu cầu người dùng commit hoặc stash các thay đổi đó trước khi tiếp tục.
2. **Đồng bộ main:**
   ```bash
   git checkout main
   git pull origin main
   ```
3. **Tạo branch và ghi nhận proposal:**
   * Tạo branch mới: `git checkout -b proposal/<tên-đề-xuất>`
   * Tạo tệp proposal tại: `<hub_path>/.agents/proposals/<YYYY-MM-DD>_<tên-đề-xuất>.md`
   
   *Cấu trúc tệp proposal:*
   ```markdown
   ---
   proposal_id: "<YYYY-MM-DD>_<tên-đề-xuất>"
   type: "<loại-đề-xuất>"
   name: "<tên-đề-xuất>"
   status: "open"
   priority: "<mức-độ-ưu-tiên>"
   proposed_by_project: "<tên-dự-án-spoke>"
   proposed_date: "<YYYY-MM-DD>"
   applies_to:
     - "<bộ-môn-áp-dụng>"
   ---
   
   ## Mô tả
   ...
   ## Vấn đề giải quyết
   ...
   ## Giải pháp / Cấu trúc đề xuất
   ...
   ```
4. **Commit & Push:**
   * Sử dụng `git add -f` đối với tệp proposal (do thư mục `.agents/` bị ignore mặc định).
   * Thực hiện commit và push:
     ```bash
     git commit -m "docs(proposal): add proposal for <tên-đề-xuất>"
     git push origin proposal/<tên-đề-xuất>
     ```

---

## Bước 4: Tạo Pull Request (PR Flow)

Kiểm tra quyền qua GitHub CLI bằng cách chạy thử `gh auth status` hoặc kiểm tra biến môi trường `GITHUB_TOKEN` / `GH_TOKEN`:
* **Nếu có quyền:** Chạy lệnh tạo PR:
  ```bash
  gh pr create --title "docs(proposal): add proposal for <tên-đề-xuất>" --body "Automated proposal submission." --base main --head proposal/<tên-đề-xuất>
  ```
* **Nếu không có quyền:** Cung cấp link tạo PR thủ công:
  👉 `https://github.com/vvChu/ccba-agent-platform/pull/new/proposal/<tên-đề-xuất>`

---

## Bước 5: Báo cáo hoàn tất

Báo cáo ngắn gọn cho người dùng bao gồm: đường dẫn tệp đề xuất, tên branch, URL của Pull Request (hoặc link tạo thủ công) và bước tiếp theo.
