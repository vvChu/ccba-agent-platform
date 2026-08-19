---
description: Đề xuất và đóng gói code/skill/workflow/tool từ Spoke lên Hub kèm Vòng lặp Dừng chờ CI & Copilot Review (Self-Healing Gate)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
disable-model-invocation: true
---
# Workflow: Propose to Hub (Đóng Góp Ngược Lên Hub Chuẩn OKF v2.0)

Quy trình chuẩn hóa toàn trình để đề xuất, đóng gói mã nguồn và hoàn tất thẩm định tự động các cải tiến từ dự án Spoke lên Platform Hub chung.

---

## 📋 Bước 1: Thu thập Thông tin & Mã Nguồn Đóng Gói
Ghi nhận đầy đủ 6 thông tin cốt lõi:
1. **Loại đề xuất:** `tool` (Package mã nguồn trong `packages/`), `skill` (Kỹ năng trong `.agents/skills/`), `workflow` (Quy trình trong `.agents/workflows/`), hoặc `rules`.
2. **Tên đề xuất:** Dạng kebab-case (ví dụ: `legislative-consolidator-okf-v2`).
3. **Mô tả & Vấn đề giải quyết:** Chi tiết nỗi đau thực tế đã giải quyết tại Spoke.
4. **Mã nguồn thực thi & Bộ test:** Đường dẫn các file code và file test tại Spoke đã vượt qua $100\%$ test cục bộ.
5. **Dự án áp dụng:** Các bộ môn áp dụng cụ thể.
6. **Mức độ ưu tiên:** "Cao" / "Trung bình" / "Thấp".

---

## 🔍 Bước 2: Kiểm tra Trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent **bắt buộc** kiểm tra hệ sinh thái Hub:
1. Đọc tệp cấu hình `.md/workspace_context.yaml` để lấy đường dẫn Hub (`hub_path`).
2. Đọc tệp catalog của Hub tại `<hub_path>/.agents/skills/platform-loader/catalog.yaml` và danh mục `packages/` để tìm kiếm thành phần tương tự.
3. Đọc tệp hiến pháp `<hub_path>/.agents/AGENTS.md` và `PLATFORM.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Đề xuất nâng cấp/mở rộng thành phần cũ thay vì tạo mới trùng lặp.

---

## 📦 Bước 3: Đóng Gói Mã Nguồn & Tạo Proposal Trên Branch Mới
Thực thi tại thư mục Hub (`hub_path`):
1. **Kiểm tra trạng thái workspace:** Đảm bảo `git status` sạch sẽ.
2. **Đồng bộ nhánh main:**
   ```bash
   git checkout main && git pull origin main
   ```
3. **Tạo branch mới:**
   ```bash
   git checkout -b proposal/[tên-đề-xuất]
   ```
4. **Đóng gói Mã nguồn & Tests vào Package tương ứng trên Hub:**
   - Copy code vào: `packages/[package-name]/src/[submodule]/`
   - Export public deep seam trong: `packages/[package-name]/src/__init__.py`
   - Copy unit/integration tests vào: `packages/[package-name]/tests/`
   - Chạy format & linting cục bộ trên Hub:
     ```bash
     python -m ruff check --fix packages/[package-name]/
     python -m ruff format packages/[package-name]/
     ```
   - Cập nhật tài liệu kiến trúc nếu có thay đổi cấu trúc:
     ```bash
     python scripts/update_arch_stats.py
     ```
5. **Ghi nhận tệp Proposal:**
   Tạo tệp tại `<hub_path>/.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md` với đầy đủ YAML frontmatter, tóm tắt kiến trúc, action tokens và kết quả kiểm thử.
6. **Commit & Push:**
   ```bash
   git add -A && git commit -m "feat([scope]): add [tên-đề-xuất] and proposal" && git push origin proposal/[tên-đề-xuất]
   ```

---

## 🚀 Bước 4: Mở GitHub Pull Request (PR Flow)
Kiểm tra quyền qua GitHub CLI:
- **Nếu có quyền:** Chạy lệnh tạo PR:
  ```bash
  gh pr create --title "feat([scope]): add [tên-đề-xuất]" --body "Automated proposal submission with implementation and test suite." --base main --head proposal/[tên-đề-xuất]
  ```
- **Nếu không có quyền:** Cung cấp link tạo PR thủ công dựa trên remote URL:
  👉 `[PR-creation-URL]/pull/new/proposal/[tên-đề-xuất]`

---

## 🔄 Bước 5: Vòng Lặp Dừng Chờ Bất Đồng Bộ & Tự Làm Xanh CI (Self-Healing Loop)

> [!IMPORTANT]
> **Tuyệt đối không kết thúc quy trình ngay sau khi mở PR.** Agent phải chủ động đồng hành cùng PR cho đến khi $100\%$ CI chuyển sang Tích Xanh.

### 5.1. Chiến Lược Dừng Chờ Động (Dynamic Grace Period & Timer Strategy)
Tùy thuộc vào khối lượng code của PR (diff size), Agent chủ động thiết lập thời gian chờ đệm để GitHub Actions khởi chạy và GitHub Copilot hoàn tất phân tích diff:
* **PR nhỏ (< 100 dòng diff):** Dừng chờ tối thiểu `45s`.
* **PR vừa (100 - 500 dòng diff):** Dừng chờ tối thiểu `60s – 90s`.
* **PR lớn (> 500 dòng diff / package mới):** Dừng chờ tối thiểu `90s – 180s`.

*(Sử dụng công cụ `schedule` để hẹn giờ kiểm tra không chiếm dụng tài nguyên).*

### 5.2. Kiểm Tra Song Song 2 Cổng (Dual-Gate Polling)
1. **Cổng 1 (GitHub Actions CI Status):**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
2. **Cổng 2 (GitHub Copilot Automated Review & Comments):**
   ```bash
   gh pr view <PR_NUMBER> --json reviews,comments --jq '.reviews[] | select(.author.login=="copilot-pull-request-reviewer")'
   ```

### 5.3. Vòng Phản Hồi & Tự Khắc Phục (Self-Healing Action)
* **Nếu CI Bị Fail:** Đọc log chi tiết qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Xác định nguyên nhân (ruff lint, mypy typing, test assertion, architecture drift) $\rightarrow$ Tự sửa code cục bộ $\rightarrow$ Commit & push bản vá lên branch PR.
* **Nếu Copilot Có Góp Ý Kỹ Thuật:** Đọc từng review comment $\rightarrow$ Đối soát với tiêu chuẩn CCBA $\rightarrow$ Thực hiện refactor sửa đổi $\rightarrow$ Commit & push.
* **Tiêu chí Hoàn Thành:** Lặp lại chu trình kiểm tra cho đến khi `gh pr checks <PR_NUMBER>` trả về exit code `0` (**`ALL CHECKS HAVE PASSED`**).

---

## ✅ Bước 6: Báo Cáo Hoàn Tất & Sẵn Sàng Merge
Sau khi toàn bộ CI đã xanh $100\%$, Agent tổng hợp báo cáo gửi người dùng:
1. **Link PR chính thức:** `https://github.com/[org]/[repo]/pull/[PR_NUMBER]`.
2. **Bảng tổng hợp kết quả CI:** Liệt kê các job tests, scan, linting đã pass.
3. **Tóm tắt các điểm đã khắc phục qua review Copilot.**
4. **Thông báo Sẵn sàng Merge:** Người dùng hoặc Maintainer có thể an tâm bấm nút Merge ngay lập tức mà không lo gãy vỡ hệ thống chung.
