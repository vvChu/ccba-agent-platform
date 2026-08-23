---
description: Thẩm định toàn trình các PR đề xuất từ Spoke lên Hub kèm Spoke Leakage
  Guard, Supervised Self-Healing và Đồng bộ Catalog Hậu Merge (ADR 0045)
applies_to:
- Tác vụ Admin
- Phần mềm
disable-model-invocation: true
---
# Workflow: Review Proposal (Thẩm Định Đề Xuất Spoke Lên Hub — ADR 0045)

Quy trình chuẩn hóa toàn trình dành cho Hub Maintainer để thẩm định, làm sạch, tự sửa lỗi có kiểm soát và hợp nhất an toàn các đề xuất (Pull Requests) từ các dự án Spoke vào Hub Monorepo.

---

## 📋 Bước 1: Tiếp Nhận & Khảo Sát Đề Xuất (Intake & Survey)

1. **Xác định PR mục tiêu:**
   - Nếu người dùng cung cấp mã PR: Sử dụng trực tiếp `#PR_NUMBER` (ví dụ: `/ccba-review-proposal 207`).
   - Nếu không chỉ định: Tự động quét danh sách các PR đề xuất đang mở:
     ```bash
     gh pr list --state open
     ```
2. **Khảo sát tệp Proposal:**
   - Kiểm tra tệp ghi nhận tại `.agents/proposals/[YYYY-MM-DD]_[name].md`.
   - Đọc YAML frontmatter (`proposal_id`, `type`, `proposed_by_project`, `priority`).
   - Đọc tóm tắt kiến trúc và mục tiêu nghiệp vụ mà Spoke đã giải quyết.

---

## 🛡️ Bước 2: Kích Hoạt Rào Chắn Rò Rỉ Spoke (Spoke Leakage Guard)

Chạy công cụ kiểm định rò rỉ tự động để đảm bảo không có tài sản cục bộ nào của Spoke lọt vào Hub:
```bash
python scripts/governance/check_spoke_leakage.py
```

**Các chốt chặn bắt buộc (Zero Tolerance):**
- ❌ Không chứa thư mục nháp/học tập của Spoke: `.md/teach/`, `.tmp/`, `.out-of-scope/`, cache.
- ❌ Không chứa đường dẫn tuyệt đối dạng Windows (`D:\...`, `C:\Users\...`) trong mã nguồn mới.
- ❌ Tệp proposal bắt buộc có đủ 4 trường metadata: `proposal_id`, `type`, `status`, `name`.

*Nếu phát hiện vi phạm:* Agent tự động loại bỏ các tệp vi phạm khỏi PR branch trước khi tiếp tục.

---

## 🧩 Bước 3: Thẩm Định Kiến Trúc Deep Seams & Kiểm Thử Độc Lập

1. **Kiểm tra ranh giới Module Sâu (Deep Seams Enforcement):**
   - Mã nguồn nghiệp vụ bắt buộc nằm gọn trong `packages/[package-name]/src/`.
   - Các entry point công khai bắt buộc được khai báo trong `__all__` tại `packages/[package-name]/src/__init__.py`.
   - Không được export bừa bãi các hàm helper nội bộ (`_helper.py`).
2. **Xác thực Bộ Kiểm thử Tự động:**
   - Chạy toàn bộ test suite của package liên quan:
     ```bash
     uv run pytest packages/[package-name]/tests
     ```
   - Chạy linter và format code:
     ```bash
     uv run ruff check packages/[package-name]
     ```
   - Tiêu chí: $100\%$ Passed, 0 errors, 0 warnings.

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
   - **Gợi ý Spoke Sync:** Thông báo danh sách Spoke downstream nên chạy `/ccba-update-spoke` để nạp tính năng mới.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
