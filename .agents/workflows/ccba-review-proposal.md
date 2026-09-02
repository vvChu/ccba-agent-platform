---
description: Thẩm định toàn trình các PR đề xuất từ Spoke lên Hub kèm Spoke Leakage
  Guard, Supervised Self-Healing và Đồng bộ Catalog Hậu Merge (ADR 0045)
bundle: _core
command: /ccba-review-proposal
triggers:
  - review proposal
  - thẩm định pr
  - duyệt đề xuất
  - review-proposal
applies_to:
- Tác vụ Admin
- Phần mềm
disable-model-invocation: true
---
# Workflow: Review Proposal (Thẩm Định Đề Xuất Spoke Lên Hub — ADR 0045)

Quy trình chuẩn hóa toàn trình dành cho Hub Maintainer để thẩm định, làm sạch, tự sửa lỗi có kiểm soát và hợp nhất an toàn các đề xuất (Pull Requests) từ các dự án Spoke vào Hub Monorepo.

---

## 📋 Bước 1: Tiếp Nhận & Khởi Tạo Môi Trường (Pre-flight Sync & Intake)

1. **Đồng bộ Base Branch (Pre-flight Sync Gate):**
   - Đảm bảo nhánh `main` local sạch và được đồng bộ với upstream trước khi thẩm định:
     ```bash
     git checkout main && git pull origin main
     ```
2. **Xác định PR mục tiêu:**
   - Nếu người dùng cung cấp mã PR: Sử dụng trực tiếp `#PR_NUMBER` (ví dụ: `/ccba-review-proposal 207` hoặc `/ccba-review-proposal 227`).
   - Nếu không chỉ định: Tự động quét danh sách các PR đề xuất đang mở:
     ```bash
     gh pr list --state open
     ```
3. **Khảo sát tệp Proposal:**
   - Kiểm tra tệp ghi nhận tại `.agents/proposals/[YYYY-MM-DD]_[name].md`.
   - Đọc YAML frontmatter (`proposal_id`, `type`, `proposed_by_project`, `priority`).
   - Đọc tóm tắt kiến trúc và mục tiêu nghiệp vụ mà Spoke đã giải quyết.

---

## 🛡️ Bước 2: Kích Hoạt 3 Worker Thẩm Định Song Song (Parallel Review Gate)

Agent điều phối 3 luồng kiểm tra song song (mô phỏng mô hình Worker của Boost):

1. **Worker 1 — Spoke Leakage & Privacy Guard:**
   - Chạy rào chắn rò rỉ và quét Maskara credentials:
     ```bash
     python scripts/governance/check_spoke_leakage.py
     ```
   - *Chốt chặn (Zero Tolerance):* Không chứa `.md/teach/`, `.tmp/`, cache, đường dẫn tuyệt đối Windows `D:\...`. Tệp proposal bắt buộc có đủ 4 trường metadata (`proposal_id`, `type`, `status`, `name`).

2. **Worker 2 — Deep Seams & Scoped Tests Verification:**
   - Kiểm tra ranh giới Module Sâu: Mã nguồn nghiệp vụ nằm gọn trong `packages/[pkg]/src/`, entry points công khai khai báo trong `__all__` tại `__init__.py`.
   - Chạy kiểm thử tự động và linter:
     ```bash
     uv run pytest packages/[package-name]/tests
     uv run ruff check packages/[package-name]
     ```
   - *Tiêu chí:* $100\%$ Passed, 0 errors, 0 warnings.

3. **Worker 3 — Proposal Lifecycle & Catalog Governance (ADR 0047):**
   - Soát chiếu metadata frontmatter của skill/workflow mới đề xuất.
   - Kiểm tra tính tương thích của `catalog.yaml` và Traceability Matrix.

---

## 🤖 Bước 4: Bóc Tách Nhận Xét Copilot & CI Checks Status

1. **Kiểm tra trạng thái GitHub Actions CI:**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
2. **Bóc tách nhận xét kỹ thuật từ GitHub Copilot:**
   ```bash
   gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq ".[] | {path: .path, line: .line, body: .body}"
   ```
3. **Phân loại nhận xét:**
   - *Lỗi kỹ thuật rõ ràng (Invalid regex, unhandled exception, syntax typo)*: Chuyển sang Bước 5 để tự động khắc phục.
   - *Góp ý thiết kế / Tài liệu*: Báo cáo Maintainer xem xét.

---

## 🛠️ Bước 5: Tự Sửa Lỗi Có Giám Sát (Supervised Self-Healing) & Hợp Nhất

1. **Khắc phục lỗi tự động trên Branch:**
   - Áp dụng các bản vá sửa regex, docstring conflict hoặc format.
   - Chạy lại `pytest` và `ruff check` để xác minh xanh $100\%$.
2. **Trình bày Diff cho Maintainer Phê Duyệt:**
   - Tóm tắt các điểm đã sửa và trình bày cho Maintainer bấm xác nhận.
3. **Hợp nhất vào nhánh `main` (Squash Merge):**
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   git checkout main && git pull origin main
   ```
4. **Quản trị Vòng đời Hậu Merge (Post-Merge Governance):**
   - **Cập nhật Proposal Header:** Đổi `status: "open"` $\rightarrow$ `status: "merged"`, ghi nhận `merged_commit` hash và `merged_date`.
   - **Đăng ký Hệ Sinh Thái (ADR 0047):** Chạy `python scripts/governance/compile_catalog.py` để tự động cập nhật `catalog.yaml` từ frontmatter của skill/workflow mới và cập nhật bảng Service Modules tại `PLATFORM.md`.
   - **Gợi ý Spoke Sync (Closed-Loop Sync):** Thông báo cho Spoke đề xuất kích hoạt **Bước 7 của `/ccba-contribute-to-hub`** (hoặc `/ccba-update-spoke`) để nạp tính năng mới và hoàn tất đóng vòng.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
